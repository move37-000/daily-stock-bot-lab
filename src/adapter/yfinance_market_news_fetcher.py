from src.domain.news import NewsItem
from src.port.market_news_fetcher import MarketNewsFetcher


class YFinanceMarketNewsFetcher(MarketNewsFetcher):
    def __init__(self, symbol: str):
        self._symbol = symbol

    def fetch(self) -> list[NewsItem]:
        raise NotImplementedError  # Adapter 단계에서 구현