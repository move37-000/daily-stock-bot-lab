from typing import Protocol

from src.domain.news import NewsItem


class MarketNewsFetcher(Protocol):
    """시장 전체 뉴스 조회 Port

    종목 뉴스(StockFetcher가 조회)와 달리 "시장 전반의 흐름을 보여주는
    뉴스"를 조회한다. 어댑터 내부 구현은 시장마다 완전히 다르다.
    미국은 S&P 500 지수에 딸린 뉴스를 쓰고, 한국은 지수 단위 뉴스 API가
    없어 대표 종목 뉴스를 모아 시장 뉴스처럼 제공한다.

    어댑터가 조회 대상(심볼·종목 리스트)을 생성자에서 주입받으므로
    fetch()는 파라미터가 없다. "어느 시장인가"는 어댑터 인스턴스 선택으로
    표현한다.
    """

    def fetch(self) -> list[NewsItem]:
        ...