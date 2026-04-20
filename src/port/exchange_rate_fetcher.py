from typing import Protocol

from src.domain.market import ExchangeRate


class ExchangeRateFetcher(Protocol):
    def fetch(self) -> ExchangeRate:
        ...