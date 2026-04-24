import logging

import yfinance as yf

from src.adapter._yfinance_common import parse_yfinance_news
from src.domain.news import NewsItem
from src.port.market_news_fetcher import MarketNewsFetcher

logger = logging.getLogger(__name__)


class YFinanceMarketNewsFetcher(MarketNewsFetcher):
    """yfinance 기반 미국 시장 뉴스 어댑터.

    S&P 500 지수(^GSPC)에 딸린 yfinance 뉴스를 시장 뉴스로 사용한다.
    yfinance가 지수 단위 뉴스를 제공하는 특성을 활용한 것이며, 한국은
    지수 단위 뉴스 API가 없어 Phase 7에서 대표 종목 뉴스 합성 방식으로
    구현 예정.

    조회 실패 시 빈 리스트를 반환한다. 시장 뉴스는 리포트의 보조 정보이므로
    실패가 리포트 본체 전송을 막지 않도록 어댑터 내부에서 격리한다.
    """

    def __init__(self, symbol: str = "^GSPC", news_limit: int = 3) -> None:
        self._symbol = symbol
        self._news_limit = news_limit

    def fetch(self) -> list[NewsItem]:
        try:
            ticker = yf.Ticker(self._symbol)
            return parse_yfinance_news(ticker, self._news_limit)
        except Exception as e:
            logger.warning(f"미국 시장 뉴스 조회 실패 ({self._symbol}): {e}")
            return []