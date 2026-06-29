"""YFinanceFetcher 어댑터 단위 테스트.

검증 책임:
1. 정상 경로 (단·다종목)
2. 단종목 실패 격리 (스킵, 예외 번역, 나머지 종목 반환)
3. 전종목 실패 시 상위로 raise (현재 RuntimeError — 코드 의도 확인 필요)
4. 뉴스 격리 (§7.9 StockFetcher 측면 — news=[]로 흡수, 스냅샷은 정상)
5. parse_yfinance_news 정상 동작 (ticker.news mock으로 간접 검증)

이 파일은 모든 어댑터 테스트 중 mock 셋업이 가장 복잡하므로
DataFrame과 yfinance 뉴스 dict 생성 헬퍼를 분리했다. 각 테스트가
중요한 차이만 짚을 수 있도록.
"""
import pandas as pd
import pytest
import requests

from src.adapter.yfinance_fetcher import YFinanceFetcher
from src.common.errors import NetworkError
from src.domain.stock import Market


# ---------- mock 데이터 헬퍼 ----------

def _history_df(closes: list[float]) -> pd.DataFrame:
    """yfinance Ticker.history(period="5d")가 반환하는 DataFrame 모킹.

    Close 값만 받고 나머지 OHLV는 적당히 채운다.
    calculate_change()가 close[-1], close[-2]만 보므로 close 정확성이 중요.
    """
    n = len(closes)
    return pd.DataFrame(
        {
            "Open": [c - 1.0 for c in closes],
            "High": [c + 1.0 for c in closes],
            "Low": [c - 2.0 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * n,
        },
        index=pd.to_datetime([f"2024-03-{18 + i:02d}" for i in range(n)]),
    )


def _yf_news_dict(
    title: str = "Apple unveils new iPhone",
    url: str = "https://news.example.com/1",
    publisher: str = "Reuters",
    pub_date: str = "2024-03-18T10:30:00Z",
) -> dict:
    """yfinance Ticker.news 응답 1건 형태."""
    return {
        "content": {
            "title": title,
            "provider": {"displayName": publisher},
            "pubDate": pub_date,
            "clickThroughUrl": {"url": url},
        }
    }


def _make_ticker(mocker, history=None, news=None, history_exc=None):
    """yf.Ticker(...) 호출이 반환할 mock 객체 1개 생성."""
    ticker = mocker.MagicMock()
    if history is not None:
        ticker.history.return_value = history
    if history_exc is not None:
        ticker.history.side_effect = history_exc
    ticker.news = news if news is not None else []
    return ticker


# ---------- 테스트 ----------

class TestNormalPath:
    def test_단일_종목_정상_반환(self, mocker):
        ticker = _make_ticker(
            mocker,
            history=_history_df([177.0, 178.5]),
            news=[_yf_news_dict()],
        )
        mocker.patch("src.adapter.yfinance_fetcher.yf.Ticker", return_value=ticker)

        result = YFinanceFetcher().fetch({"AAPL": "Apple"})

        assert len(result) == 1
        snap = result[0]
        assert snap.symbol == "AAPL"
        assert snap.name == "Apple"
        assert snap.market is Market.US
        assert snap.close == 178.5
        assert snap.change == pytest.approx(1.5)
        # 178.5 - 177.0 = 1.5, 1.5/177.0 * 100 ≈ 0.847
        assert snap.change_pct == pytest.approx(0.847, abs=0.01)
        assert len(snap.history) == 2
        assert len(snap.news) == 1

    def test_다종목_모두_정상(self, mocker):
        """yf.Ticker 호출 순서대로 다른 mock 반환 (dict iteration 순서 = 호출 순서)."""
        aapl = _make_ticker(mocker, history=_history_df([177.0, 178.5]))
        msft = _make_ticker(mocker, history=_history_df([395.0, 400.0]))
        mocker.patch(
            "src.adapter.yfinance_fetcher.yf.Ticker",
            side_effect=[aapl, msft],
        )

        result = YFinanceFetcher().fetch({"AAPL": "Apple", "MSFT": "Microsoft"})

        assert len(result) == 2
        assert result[0].symbol == "AAPL"
        assert result[1].symbol == "MSFT"


class TestPartialFailureIsolation:
    """단종목 실패는 격리되고 나머지 종목 반환."""

    def test_history_empty_종목_스킵(self, mocker):
        """경계: 빈 DataFrame은 ParseError가 아닌 '데이터 없음' 의미.

        상장 폐지·잘못된 심볼 등 상시 발생 시나리오. 해당 종목만 스킵하고
        나머지가 있으면 그것을 반환. errors 리스트에도 안 들어감.
        """
        empty = _make_ticker(mocker, history=pd.DataFrame())
        aapl = _make_ticker(mocker, history=_history_df([177.0, 178.5]))
        mocker.patch(
            "src.adapter.yfinance_fetcher.yf.Ticker",
            side_effect=[empty, aapl],
        )

        result = YFinanceFetcher().fetch({"BAD": "Bad", "AAPL": "Apple"})

        assert len(result) == 1
        assert result[0].symbol == "AAPL"

    def test_RequestException_종목_제외하고_나머지_반환(self, mocker):
        """단종목 RequestException → NetworkError 번역 → for문이 흡수."""
        bad = _make_ticker(
            mocker, history_exc=requests.RequestException("connection lost"),
        )
        aapl = _make_ticker(mocker, history=_history_df([177.0, 178.5]))
        mocker.patch(
            "src.adapter.yfinance_fetcher.yf.Ticker",
            side_effect=[bad, aapl],
        )

        result = YFinanceFetcher().fetch({"BAD": "Bad", "AAPL": "Apple"})

        assert len(result) == 1
        assert result[0].symbol == "AAPL"

    def test_파싱_예외_종목_제외하고_나머지_반환(self, mocker):
        """KeyError 등 → ParseError 번역 → for문이 흡수.

        ParseError 자체는 @retry 비대상(_is_retryable=False)이지만,
        단종목 단위로는 for문이 흡수하므로 fetch() 호출 전체가 깨지지 않음.
        """
        # Close 컬럼이 없는 broken DataFrame
        broken_df = pd.DataFrame(
            {"Wrong": [1, 2]},
            index=pd.to_datetime(["2024-03-18", "2024-03-19"]),
        )
        bad = _make_ticker(mocker, history=broken_df)
        aapl = _make_ticker(mocker, history=_history_df([177.0, 178.5]))
        mocker.patch(
            "src.adapter.yfinance_fetcher.yf.Ticker",
            side_effect=[bad, aapl],
        )

        result = YFinanceFetcher().fetch({"BAD": "Bad", "AAPL": "Apple"})

        assert len(result) == 1
        assert result[0].symbol == "AAPL"


class TestAllFailure:
    """전종목 실패 시 상위로 NetworkError raise → @retry 발동.

    이게 docstring 약속의 핵심: 전종목 동시 실패는 yfinance 일시 장애로 해석,
    2초 후 재시도로 자동 복구를 시도한다. 단종목 실패는 for문이 흡수하므로
    @retry가 발동할 일이 없다.
    """

    def test_전종목_실패시_NetworkError(self, mocker):
        """전종목 실패 → NetworkError로 raise.

        @retry가 발동해 3회 시도하므로 time.sleep을 mock해야 테스트가 빠르다.
        side_effect를 함수로 둬 매 호출마다 새 mock 반환 (3시도 × 2종목 = 6회).
        """
        mocker.patch("src.common.retry.time.sleep")

    def _failing_ticker(*_args, **_kwargs):
        t = mocker.MagicMock()
        t.history.side_effect = requests.RequestException("conn lost")
        return t

    mocker.patch(
        "src.adapter.yfinance_fetcher.yf.Ticker",
        side_effect=_failing_ticker,
    )

    with pytest.raises(NetworkError, match="모든 미국 종목 조회 실패"):
        YFinanceFetcher().fetch({"AAPL": "Apple", "MSFT": "Microsoft"})

    def test_전종목_실패시_retry_3회_발동(self, mocker):
        """전종목 실패의 부가 검증: @retry가 정확히 3회 시도, sleep 2회.

        앞 테스트와 같은 시나리오지만 관심사가 다르다.
        예외 타입은 위에서 검증, 여기는 retry 동작 보장.
        """
        mock_sleep = mocker.patch("src.common.retry.time.sleep")
        ticker_call_count = 0