from typing import Protocol

from src.domain.stock import StockSnapshot


class StockFetcher(Protocol):
    """종목 시세 조회 Port

    어댑터는 주가와 종목 뉴스를 함께 조회하여 완성된 StockSnapshot을
    반환한다. 뉴스 조회 실패가 전체 조회 실패로 전파되지 않도록 어댑터
    내부에서 격리한다 (뉴스 실패 시 news=[]).

    입력은 (심볼 → 표시 이름) 매핑. 미국은 티커=이름으로 쓰였으나
    Phase 2부터 config에서 표시 이름을 별도로 관리한다.
    """

    def fetch(self, tickers: dict[str, str]) -> list[StockSnapshot]:
        ...