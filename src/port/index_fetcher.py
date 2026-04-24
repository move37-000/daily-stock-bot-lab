from typing import Protocol

from src.domain.market import IndexSnapshot


class IndexFetcher(Protocol):
    """시장 지수 조회 Port

        지수 1개 단위로 조회한다. 시장 단위(primary + secondary)를 한 번에
        반환하지 않는 이유는 FallbackIndexFetcher(Phase 7)가 지수별로 독립 폴백해야
        하기 때문이다. KOSPI는 KRX API로 성공했지만 KOSDAQ만 실패하는
        경우에도 KOSDAQ만 네이버 금융으로 폴백할 수 있어야 한다.

        심볼만으로는 표시 이름(예: "S&P 500")을 알 수 없어 호출측이 (symbol, name)을
        함께 전달한다. StockFetcher.fetch(dict[str, str])와 구조 대칭.
        """

    def fetch(self, symbol: str, name: str) -> IndexSnapshot:
        ...