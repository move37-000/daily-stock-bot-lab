from typing import Protocol

from src.domain.news import NewsItem


class MarketNewsFetcher(Protocol):
    def fetch(self) -> list[NewsItem]:
        ...