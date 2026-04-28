import logging

import pandas as pd
import yfinance as yf

from src.adapter._yfinance_common import calculate_change
from src.domain.market import PricePoint, IndexSnapshot
from src.port.index_fetcher import IndexFetcher

logger = logging.getLogger(__name__)

class YFinanceIndexFetcher(IndexFetcher):
    """yfinance 기반 시장 지수 어댑터.

    S&P 500, NASDAQ 등 미국 지수 조회를 담당한다. 한국 지수(KOSPI, KOSDAQ)는
    Phase 7에서 KRX API 기반 어댑터로 별도 구현 예정 (STRUCTURE §7.5).

    데이터 부족(히스토리 2일 미만) 또는 조회 실패 시 RuntimeError를 던진다.
    실패를 기본값으로 위장하지 않는다 (§6.16 실패는 예외 원칙).
    """

    _BUFFER_DAYS = 2  # 주말/공휴일로 인한 거래일 부족 커버용 버퍼

    def __init__(self, history_days: int = 5) -> None:
        self._history_days = history_days

    def fetch(self, symbol: str, name: str) -> IndexSnapshot:
        ticker = yf.Ticker(symbol)
        period = f"{self._history_days + self._BUFFER_DAYS}d"
        history = ticker.history(period=period)

        if len(history) < 2:
            raise RuntimeError(
                f"{name} ({symbol}) 지수 데이터 부족: {len(history)}일치"
            )

        history = history.tail(self._history_days)
        close, change, change_pct = calculate_change(history)
        stock_daily = self._parse_history(history)

        return IndexSnapshot(
            name=name,
            price=close,
            change=change,
            change_pct=change_pct,
            history=stock_daily,
        )

    @staticmethod
    def _parse_history(history: pd.DataFrame) -> list[PricePoint]:
        return [
            PricePoint(
                date=date.strftime("%Y-%m-%d"),
                open=float(row["Close"]),
                high=float(row["Close"]),
                low=float(row["Close"]),
                close=float(row["Close"]),
                volume=0,
            )
            for date, row in history.iterrows()
        ]