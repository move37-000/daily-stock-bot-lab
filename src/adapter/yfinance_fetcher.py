from src.domain.stock import StockSnapshot
from src.port.stock_fetcher import StockFetcher


class YFinanceFetcher(StockFetcher):
    def fetch(self, tickers: dict[str, str]) -> list[StockSnapshot]:
        raise NotImplementedError 