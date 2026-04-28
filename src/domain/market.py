from dataclasses import dataclass, field

from src.domain.stock import StockDaily, PricePoint, Market


@dataclass(frozen=True)
class PricePoint:
    """가격 시계열 점 (지수·환율 스파크라인용).

    종목과 달리 OHLCV 중 종가만 의미가 있는 데이터에 사용한다. 종목용
    OHLCV 타입은 StockDaily.

    Phase 2 보정으로 신설. Phase 1 도메인 설계는 DailyPrice(OHLCV) 하나로
    종목/지수/환율을 모두 표현하려 했으나, 지수/환율 어댑터에서 억지 채우기
    어색함이 드러났다 (DailyPrice(open=close, high=close, low=close,
    close=close, volume=0)).
    """
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
