import pandas as pd
import yfinance as yf

from src.domain.market import PricePoint
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


def parse_price_history(history: pd.DataFrame) -> list[PricePoint]:
    """yfinance history DataFrame을 PricePoint 리스트로 변환.

    지수·환율 어댑터가 스파크라인 시계열을 만들 때 공유한다 (종가만 사용).
    종목용 OHLCV 변환(StockDaily)과는 별개 — 그쪽은 전체 필드를 보존한다.
    """
    return [
        PricePoint(date=ts.strftime("%Y-%m-%d"), price=float(row["Close"]))
        for ts, row in history.iterrows()
    ]


def parse_yfinance_news(ticker: yf.Ticker, limit: int) -> list[NewsItem]:
    """yfinance Ticker에서 뉴스를 파싱해 NewsItem 리스트로 변환.

    종목 뉴스(StockFetcher)와 시장 뉴스(MarketNewsFetcher) 어댑터가 공유한다.
    파싱 자체는 실패 격리를 하지 않는다. 실패 격리 정책은 호출측 어댑터가
    Port 규약에 따라 결정한다:
    - StockFetcher: 뉴스 실패는 news=[]로 격리 (종목 전체 조회 실패 아님)
    - MarketNewsFetcher: 뉴스 실패는 []로 격리 (리포트 본체를 막지 않음)
    """
    return [_parse_news_item(item) for item in ticker.news[:limit]]


def _parse_news_item(item: dict) -> NewsItem:
    """단일 yfinance 뉴스 아이템 → NewsItem.

    yfinance 응답은 키가 존재하되 값이 None인 경우가 있다(예: 페이월 기사의
    clickThroughUrl=None). dict.get(k, {})의 기본값은 '키 부재'만 커버하고
    'None 값'은 못 잡으므로, 중첩 dict는 `get(k) or {}`로 폴백한다.
    """
    content = item.get("content") or {}
    return NewsItem(
        title=content.get("title") or "",
        link=_extract_news_link(content),
        publisher=(content.get("provider") or {}).get("displayName", ""),
        time=format_us_news_time(content.get("pubDate") or ""),
    )


def _extract_news_link(content: dict) -> str:
    """yfinance 뉴스 응답에서 링크 추출. clickThroughUrl 우선, canonicalUrl 폴백.

    값이 None일 수 있어(페이월 기사 등) `get(k) or {}`로 방어한다.
    """
    click = content.get("clickThroughUrl") or {}
    canonical = content.get("canonicalUrl") or {}
    return click.get("url", "") or canonical.get("url", "")