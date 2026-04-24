import pandas as pd
import yfinance as yf

from src.common.date_utils import format_us_news_time
from src.domain.news import NewsItem


def calculate_change(history: pd.DataFrame) -> tuple[float, float, float]:
    """yfinance history DataFrame에서 (최신 종가, 전일 대비 변동, 변동률%) 계산.

    종목·지수·환율 어댑터가 공유하는 순수 계산 로직. history는 최소 2일치
    데이터를 포함해야 하며, 호출측에서 len(history) >= 2를 보장해야 한다.
    """
    latest = history.iloc[-1]
    prev = history.iloc[-2]
    close = float(latest["Close"])
    prev_close = float(prev["Close"])
    change = close - prev_close
    change_pct = (change / prev_close) * 100
    return close, change, change_pct


def parse_yfinance_news(ticker: yf.Ticker, limit: int) -> list[NewsItem]:
    """yfinance Ticker에서 뉴스를 파싱해 NewsItem 리스트로 변환.

    종목 뉴스(StockFetcher)와 시장 뉴스(MarketNewsFetcher) 어댑터가 공유한다.
    파싱 자체는 실패 격리를 하지 않는다. 실패 격리 정책은 호출측 어댑터가
    Port 규약에 따라 결정한다:
    - StockFetcher: 뉴스 실패는 news=[]로 격리 (종목 전체 조회 실패 아님)
    - MarketNewsFetcher: 뉴스 실패는 []로 격리 (리포트 본체를 막지 않음)
    """
    return [
        NewsItem(
            title=item.get("content", {}).get("title", ""),
            link=_extract_news_link(item.get("content", {})),
            publisher=(
                item.get("content", {})
                .get("provider", {})
                .get("displayName", "")
            ),
            time=format_us_news_time(item.get("content", {}).get("pubDate", "")),
        )
        for item in ticker.news[:limit]
    ]


def _extract_news_link(content: dict) -> str:
    """yfinance 뉴스 응답에서 링크 추출. clickThroughUrl 우선, canonicalUrl 폴백."""
    return (
        content.get("clickThroughUrl", {}).get("url", "")
        or content.get("canonicalUrl", {}).get("url", "")
    )
