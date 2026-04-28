from dataclasses import dataclass, field
from enum import Enum

from src.domain.news import NewsItem


class Market(Enum):
    """시장 구분"""
    US = "US"
    KR = "KR"


@dataclass(frozen=True)
class StockDaily:
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
    history: list[PricePoint] = field(default_factory=list)
    news: list[NewsItem] = field(default_factory=list)

    @property
    def is_up(self) -> bool:
        """상승 여부 (0 포함)"""
        return self.change >= 0

    @property
    def formatted_change_pct(self) -> str:
        """부호 포함 변동률 (예: '+1.73', '-0.45')"""
        return f"{self.change_pct:+.2f}"

    @property
    def emoji(self) -> str:
        return "🟢" if self.is_up else "🔴"

    @property
    def formatted_price(self) -> str:
        if self.market == Market.KR:
            return f"{int(self.close):,}"
        return f"{self.close:,.2f}"