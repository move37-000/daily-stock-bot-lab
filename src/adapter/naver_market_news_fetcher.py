from src.domain.news import NewsItem
from src.port.market_news_fetcher import MarketNewsFetcher


class NaverMarketNewsFetcher(MarketNewsFetcher):
    def __init__(self, representative_codes: list[str]):
        self._codes = representative_codes

    def fetch(self) -> list[NewsItem]:
        raise NotImplementedError  # Adapter 단계에서 구현