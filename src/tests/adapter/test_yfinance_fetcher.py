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