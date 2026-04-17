from typing import Protocol

from src.domain.stock import StockSnapshot


class StockFetcher(Protocol):
    def fetch(self, tickers: dict[str, str]) -> list[StockSnapshot]:
        ...