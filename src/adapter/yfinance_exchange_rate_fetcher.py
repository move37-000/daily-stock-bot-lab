import requests
import yfinance as yf

from src.adapter._yfinance_common import calculate_change, parse_price_history
from src.common.errors import NetworkError, ParseError
from src.common.retry import retry
from src.domain.market import ExchangeRate
from src.port.exchange_rate_fetcher import ExchangeRateFetcher


class YFinanceExchangeRateFetcher(ExchangeRateFetcher):
    """yfinance 기반 환율 어댑터.

    USD/KRW 등 환율 쌍을 조회한다. 지수 어댑터와 동일하게 스파크라인용
    history(종가 시계열)를 함께 반환한다 (Phase 5 복원).

    조회 실패는 NetworkError, 데이터 부족(2일 미만)·파싱 실패는 ParseError로
    번역한다. @retry는 NetworkError / 5xx만 흡수하고 데이터 부족은 즉시 실패.
    """

    _BUFFER_DAYS = 2  # 주말/공휴일로 인한 거래일 부족 커버용 버퍼

    def __init__(
        self,
        symbol: str = "USDKRW=X",
        pair: str = "USD/KRW",
        history_days: int = 5,
    ) -> None:
        self._symbol = symbol
        self._pair = pair
        self._history_days = history_days

    @retry(max_attempts=3, delay=2.0)
    def fetch(self) -> ExchangeRate:
        try:
            ticker = yf.Ticker(self._symbol)
            period = f"{self._history_days + self._BUFFER_DAYS}d"
            history = ticker.history(period=period)
        except requests.RequestException as e:
            raise NetworkError(f"yfinance 연결 실패 ({self._pair}, {self._symbol})") from e

        if len(history) < 2:
            # 데이터 부족은 재시도해도 같은 결과 → ParseError로 즉시 실패.
            raise ParseError(
                f"{self._pair} ({self._symbol}) 환율 데이터 부족: {len(history)}일치"
            )

        try:
            history = history.tail(self._history_days)
            close, change, change_pct = calculate_change(history)
            price_points = parse_price_history(history)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            raise ParseError(f"yfinance 응답 파싱 실패 ({self._pair}, {self._symbol})") from e

        return ExchangeRate(
            pair=self._pair,
            price=close,
            change=change,
            change_pct=change_pct,
            history=price_points,
        )