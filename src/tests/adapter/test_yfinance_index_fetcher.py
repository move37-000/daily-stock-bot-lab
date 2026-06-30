"""YFinanceIndexFetcher 어댑터 단위 테스트.

검증 책임:
1. 정상 경로 — IndexSnapshot 반환, history(PricePoint) 변환
2. 데이터 부족(2일 미만) → ParseError 즉시 실패 (RuntimeError 버그 수정 회귀 방지)
3. 조회 실패(RequestException) → NetworkError 번역 + @retry 3회
4. 파싱 실패(Close 컬럼 없음) → ParseError

지수 어댑터는 종목과 달리 단일 ticker 단위라 for-격리가 없다.
실패는 fetch() 전체를 raise로 전파한다.
"""
import pandas as pd
import pytest
import requests

from src.adapter.yfinance_index_fetcher import YFinanceIndexFetcher
from src.common.errors import NetworkError, ParseError


def _history_df(closes: list[float]) -> pd.DataFrame:
    """Close 컬럼 + DatetimeIndex만 채운다.

    calculate_change는 Close[-1]·Close[-2]만, parse_price_history는 Close +
    인덱스 날짜만 사용하므로 그 외 컬럼은 불필요.
    """
    n = len(closes)
    return pd.DataFrame(
        {"Close": closes},
        index=pd.to_datetime([f"2024-03-{18 + i:02d}" for i in range(n)]),
    )


def _make_ticker(mocker, history=None, history_exc=None):
    ticker = mocker.MagicMock()
    if history is not None:
        ticker.history.return_value = history
    if history_exc is not None:
        ticker.history.side_effect = history_exc
    return ticker


class TestNormalPath:
    def test_정상_IndexSnapshot_반환(self, mocker):
        ticker = _make_ticker(mocker, history=_history_df([5180.0, 5200.0]))
        mocker.patch(
            "src.adapter.yfinance_index_fetcher.yf.Ticker", return_value=ticker
        )

        result = YFinanceIndexFetcher().fetch("^GSPC", "S&P 500")

        assert result.name == "S&P 500"
        assert result.price == 5200.0
        assert result.change == pytest.approx(20.0)
        # 20 / 5180 * 100 ≈ 0.386
        assert result.change_pct == pytest.approx(0.386, abs=0.01)

    def test_history가_PricePoint로_변환(self, mocker):
        ticker = _make_ticker(mocker, history=_history_df([5180.0, 5200.0]))
        mocker.patch(
            "src.adapter.yfinance_index_fetcher.yf.Ticker", return_value=ticker
        )

        result = YFinanceIndexFetcher().fetch("^GSPC", "S&P 500")

        assert len(result.history) == 2
        assert result.history[0].date == "2024-03-18"
        assert result.history[0].price == 5180.0
        assert result.history[-1].price == 5200.0


class TestDataShortage:
    """데이터 부족 → ParseError 즉시 실패. RuntimeError 회귀 방지."""

    def test_2일_미만_ParseError(self, mocker):
        ticker = _make_ticker(mocker, history=_history_df([5200.0]))
        mocker.patch(
            "src.adapter.yfinance_index_fetcher.yf.Ticker", return_value=ticker
        )

        with pytest.raises(ParseError, match="데이터 부족"):
            YFinanceIndexFetcher().fetch("^GSPC", "S&P 500")

    def test_데이터_부족은_retry_안함(self, mocker):
        """ParseError는 _is_retryable=False → sleep 0회 (헛돌지 않음 보장)."""
        mock_sleep = mocker.patch("src.common.retry.time.sleep")
        ticker = _make_ticker(mocker, history=_history_df([5200.0]))
        mocker.patch(
            "src.adapter.yfinance_index_fetcher.yf.Ticker", return_value=ticker
        )

        with pytest.raises(ParseError):
            YFinanceIndexFetcher().fetch("^GSPC", "S&P 500")

        assert mock_sleep.call_count == 0


class TestNetworkFailure:
    def test_RequestException_NetworkError_번역(self, mocker):
        mocker.patch("src.common.retry.time.sleep")
        ticker = _make_ticker(
            mocker, history_exc=requests.RequestException("conn lost")
        )
        mocker.patch(
            "src.adapter.yfinance_index_fetcher.yf.Ticker", return_value=ticker
        )

        with pytest.raises(NetworkError, match="yfinance 연결 실패"):
            YFinanceIndexFetcher().fetch("^GSPC", "S&P 500")

    def test_NetworkError_retry_3회(self, mocker):
        mock_sleep = mocker.patch("src.common.retry.time.sleep")
        call_count = 0

        def _failing_ticker(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            t = mocker.MagicMock()
            t.history.side_effect = requests.RequestException("conn lost")
            return t

        mocker.patch(
            "src.adapter.yfinance_index_fetcher.yf.Ticker",
            side_effect=_failing_ticker,
        )

        with pytest.raises(NetworkError):
            YFinanceIndexFetcher().fetch("^GSPC", "S&P 500")

        assert call_count == 3              # @retry max_attempts=3
        assert mock_sleep.call_count == 2   # 시도 사이 2회


class TestParseFailure:
    def test_Close_컬럼_없으면_ParseError(self, mocker):
        broken = pd.DataFrame(
            {"Wrong": [1, 2]},
            index=pd.to_datetime(["2024-03-18", "2024-03-19"]),
        )
        ticker = _make_ticker(mocker, history=broken)
        mocker.patch(
            "src.adapter.yfinance_index_fetcher.yf.Ticker", return_value=ticker
        )

        with pytest.raises(ParseError, match="파싱 실패"):
            YFinanceIndexFetcher().fetch("^GSPC", "S&P 500")