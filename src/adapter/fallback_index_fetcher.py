from src.domain.market import IndexSnapshot
from src.port.index_fetcher import IndexFetcher


class FallbackIndexFetcher(IndexFetcher):
    def __init__(self, fetchers: list[IndexFetcher]):
        self._fetchers = fetchers

    def fetch(self, symbol: str) -> IndexSnapshot:
        for fetcher in self._fetchers:
            try:
                return fetcher.fetch(symbol)
            except Exception:  # Phase 3에서 예외 계층으로 세분화
                continue
        raise RuntimeError(f"All fetchers failed for {symbol}")