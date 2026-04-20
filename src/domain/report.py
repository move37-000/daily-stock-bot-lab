from dataclasses import dataclass
from datetime import date
from src.domain.stock import StockSnapshot
from src.domain.market import MarketOverview, ExchangeRate

@dataclass(frozen=True)
class DailyReport:
    date: date
    us_stocks: list[StockSnapshot]
    kr_stocks: list[StockSnapshot]
    us_market: MarketOverview
    kr_market: MarketOverview
    exchange_rate: ExchangeRate

    @property
    def us_up_count(self) -> int:
        return sum(1 for s in self.us_stocks if s.is_up)

    @property
    def kr_up_count(self) -> int:
        return sum(1 for s in self.kr_stocks if s.is_up)

    @property
    def top_gainer(self) -> StockSnapshot:
        return max(self.us_stocks + self.kr_stocks, key=lambda s: s.change_pct)

    @property
    def top_loser(self) -> StockSnapshot:
        return min(self.us_stocks + self.kr_stocks, key=lambda s: s.change_pct)