from typing import Protocol

from src.domain.news import NewsItem


class MarketNewsFetcher(Protocol):
    """시장 전체 뉴스 조회 Port

    종목 뉴스(StockFetcher가 조회)와 달리 "시장 전반의 흐름을 보여주는
    뉴스"를 조회한다. 어댑터 내부 구현은 시장마다 완전히 다르다.
    미국은 S&P 500 지수에 딸린 뉴스를 쓰고, 한국은 지수 단위 뉴스 API가
    없어 대표 종목 뉴스를 모아 시장 뉴스처럼 제공한다 (Phase 7).

    어댑터가 조회 대상(심볼·종목 리스트)을 생성자에서 주입받으므로
    fetch()는 파라미터가 없다. "어느 시장인가"는 어댑터 인스턴스 선택으로
    표현한다.

    시장 뉴스는 리포트의 보조 정보이므로 조회 실패 시 빈 리스트([])를
    반환한다. 리포트 본체(주가·지수·환율)가 뉴스 실패로 막히지 않도록
    어댑터 내부에서 격리한다. StockFetcher의 뉴스 실패 격리와 같은 성격
    (§6.16 '실패는 예외' 원칙의 Port별 예외 규약).
    """

    def fetch(self) -> list[NewsItem]:
        ...