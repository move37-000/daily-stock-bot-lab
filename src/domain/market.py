from dataclasses import dataclass, field

from src.domain.stock import PricePoint, Market


@dataclass(frozen=True)
class PricePoint:
    date: str
    price: float


@dataclass(frozen=True)
class IndexSnapshot:
    """시장 지수 스냅샷 (S&P 500, KOSPI 등)

    원본값(숫자)만 저장하고, 표현(포맷팅/emoji)은 property로 계산한다.
    """
    name: str
    price: float
    change: float
    change_pct: float
    history: list[PricePoint] = field(default_factory=list)

    @property
    def is_up(self) -> bool:
        """상승 여부 (0 포함)"""
        return self.change >= 0

    @property
    def formatted_price(self) -> str:
        """천단위 콤마 + 소수점 2자리 (예: '5,234.56')"""
        return f"{self.price:,.2f}"

    @property
    def formatted_change_pct(self) -> str:
        """부호 포함 변동률 (예: '+1.73', '-0.45')"""
        return f"{self.change_pct:+.2f}"

    @property
    def emoji(self) -> str:
        return "🟢" if self.is_up else "🔴"


@dataclass(frozen=True)
class MarketOverview:
    """미국/한국 시장의 주요 지수 요약"""
    market: Market
    primary: IndexSnapshot
    secondary: IndexSnapshot


@dataclass(frozen=True)
class ExchangeRate:
    """환율 스냅샷 (USD/KRW 등)"""
    pair: str
    price: float
    change: float
    change_pct: float

    @property
    def is_up(self) -> bool:
        """상승 여부 (0 포함)"""
        return self.change >= 0

    @property
    def formatted_price(self) -> str:
        """천단위 콤마 + 소수점 2자리 (예: '5,234.56')"""
        return f"{self.price:,.2f}"

    @property
    def formatted_change_pct(self) -> str:
        """부호 포함 변동률 (예: '+1.73', '-0.45')"""
        return f"{self.change_pct:+.2f}"
