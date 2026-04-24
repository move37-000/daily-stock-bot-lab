import yfinance as yf

from src.adapter._yfinance_common import calculate_change
from src.domain.market import ExchangeRate
from src.port.exchange_rate_fetcher import ExchangeRateFetcher


class YFinanceExchangeRateFetcher(ExchangeRateFetcher):
    """yfinance 기반 환율 어댑터.

    USD/KRW 등 환율 쌍을 조회한다. ExchangeRate는 history 필드를 갖지 않으므로
    전일 대비 계산에 필요한 최소 데이터(2일치)만 요청한다.

    데이터 부족 또는 조회 실패 시 RuntimeError를 던진다.
    """

    _PERIOD = "5d"  # 2일 + 주말/공휴일 버퍼

    def __init__(
        self,
        symbol: str = "USDKRW=X",
        pair: str = "USD/KRW",
    ) -> None:
        self._symbol = symbol
        self._pair = pair

    def fetch(self) -> ExchangeRate:
        ticker = yf.Ticker(self._symbol)
        history = ticker.history(period=self._PERIOD)

        if len(history) < 2:
            raise RuntimeError(
                f"{self._pair} ({self._symbol}) 환율 데이터 부족: {len(history)}일치"
            )

        close, change, change_pct = calculate_change(history)

        return ExchangeRate(
            pair=self._pair,
            price=close,
            change=change,
            change_pct=change_pct,
        )