from dataclasses import dataclass, field
from enum import Enum

from src.domain.news import NewsItem


class Market(Enum):
    """시장 구분"""
    US = "US"
    KR = "KR"


@dataclass(frozen=True)
class DailyPrice:
    """하루치 OHLCV 시세 데이터"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class StockSnapshot:
    """특정 시점의 종목 스냅샷

    크롤러(어댑터)와 서비스 레이어 사이의 '계약'이 되는 타입.
    """
    symbol: str
    name: str
    market: Market
    close: float
    change: float
    change_pct: float
    history: list[DailyPrice] = field(default_factory=list)
    news: list[NewsItem] = field(default_factory=list)