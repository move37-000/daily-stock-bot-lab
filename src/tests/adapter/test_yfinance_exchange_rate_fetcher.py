"""YFinanceExchangeRateFetcher 어댑터 단위 테스트.

검증 책임:
1. 정상 경로 — ExchangeRate 반환, history(PricePoint) 변환 (Phase 5 복원)
2. 데이터 부족(2일 미만) → ParseError 즉시 실패
3. 조회 실패(RequestException) → NetworkError 번역 + @retry 3회
4. 파싱 실패(Close 컬럼 없음) → ParseError

지수 어댑터와 평행 구조. 헬퍼·검증 패턴을 동일하게 둔다.
"""
import pandas as pd
import pytest
import requests

from src.adapter.yfinance_exchange_rate_fetcher import YFinanceExchangeRateFetcher
from src.common.errors import NetworkError, ParseError


def _history_df(closes: list[float]) -> pd.DataFrame:
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
    def test_정상_ExchangeRate_반환(self, mocker):
        ticker = _make_ticker(mocker, history=_history_df([1335.0, 1340.5]))
        mocker.patch(
            "src.adapter.yfinance_exchange_rate_fetcher.yf.Ticker",
            return_value=ticker,
        )

        result = YFinanceExchangeRateFetcher().fetch()

        assert result.pair == "USD/KRW"
        assert result.price == 1340.5
        assert result.change == pytest.approx(5.5)

    def test_history가_PricePoint로_변환(self, mocker):
        ticker = _make_ticker(mocker, history=_history_df([1335.0, 1340.5]))
        mocker.patch(
            "src.adapter.yfinance_exchange_rate_fetcher.yf.Ticker",
            return_value=ticker,
        )

        result = YFinanceExchangeRateFetcher().fetch()

        assert len(result.history) == 2
        assert result.history[0].date == "2024-03-18"
        assert result.history[-1].price == 1340.5


class TestDataShortage:
    def test_2일_미만_ParseError(self, mocker):
        ticker = _make_ticker(mocker, history=_history_df([1340.5]))
        mocker.patch(
            "src.adapter.yfinance_exchange_rate_fetcher.yf.Ticker",
            return_value=ticker,
        )

        with pytest.raises(ParseError, match="데이터 부족"):
            YFinanceExchangeRateFetcher().fetch()

    def test_데이터_부족은_retry_안함(self, mocker):
        mock_sleep = mocker.patch("src.common.retry.time.sleep")
        ticker = _make_ticker(mocker, history=_history_df([1340.5]))
        mocker.patch(
            "src.adapter.yfinance_exchange_rate_fetcher.yf.Ticker",
            return_value=ticker,
        )

        with pytest.raises(ParseError):
            YFinanceExchangeRateFetcher().fetch()

        assert mock_sleep.call_count == 0


class TestNetworkFailure:
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
            "src.adapter.yfinance_exchange_rate_fetcher.yf.Ticker",
            side_effect=_failing_ticker,
        )

        with pytest.raises(NetworkError, match="yfinance 연결 실패"):
            YFinanceExchangeRateFetcher().fetch()

        assert call_count == 3
        assert mock_sleep.call_count == 2


class TestParseFailure:
    def test_Close_컬럼_없으면_ParseError(self, mocker):
        broken = pd.DataFrame(
            {"Wrong": [1, 2]},
            index=pd.to_datetime(["2024-03-18", "2024-03-19"]),
        )
        ticker = _make_ticker(mocker, history=broken)
        mocker.patch(
            "src.adapter.yfinance_exchange_rate_fetcher.yf.Ticker",
            return_value=ticker,
        )

        with pytest.raises(ParseError, match="파싱 실패"):
            YFinanceExchangeRateFetcher().fetch()