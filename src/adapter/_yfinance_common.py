import logging

import pandas as pd
import yfinance as yf

from src.domain.market import PricePoint
from src.common.date_utils import format_us_news_time
from src.domain.news import NewsItem

logger = logging.getLogger(__name__)


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


def has_nan_close(history: pd.DataFrame) -> bool:
    """history의 Close 컬럼에 NaN이 섞였는지.

    야후가 간헐적으로 마지막 거래일 종가만 null로 내려보내는 사고를 감지한다.
    yfinance의 keepna=False는 OHLCV가 **전부** NaN/0일 때만 행을 버리므로
    (scrapers/history.py의 `.all(axis=1)`), Close만 깨진 행은 그대로 통과한다.
    history.empty도 False가 되어 기존 방어선에 걸리지 않는다.

    판정만 한다. 막을지 기록만 할지는 호출측 어댑터가 정한다.
    """
    if "Close" not in history.columns:
        return False
    return bool(history["Close"].isna().any())


def safe_history_metadata(ticker: yf.Ticker) -> dict | None:
    """ticker.history_metadata를 안전하게 읽는다. 실패하면 None.

    야후가 그 시점 시장 상태를 뭐라고 인식했는지(regularMarketTime,
    exchangeTimezoneName, currentTradingPeriod)가 담겨 있어 사고 분석에 쓸모가 있다.

    try/except로 감싸는 이유: 캐시에 tradingPeriods가 없으면 이 프로퍼티가
    **추가 네트워크 요청을 날린다**(yfinance/scrapers/history.py의 get_history_metadata).
    야후가 이상하게 굴고 있는 바로 그 순간에 호출되므로 행·타임아웃 위험이 있다.
    메타를 못 얻더라도 DataFrame 덤프는 반드시 남아야 하므로 여기서 격리한다.
    """
    try:
        metadata = ticker.history_metadata
    except Exception as e:
        logger.warning(f"history_metadata 조회 실패: {e}")
        return None
    return metadata if isinstance(metadata, dict) else None


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