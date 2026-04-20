from typing import Protocol
from src.domain.market import IndexSnapshot

class IndexFetcher(Protocol):
    def fetch(self, symbol: str) -> IndexSnapshot:
        ...