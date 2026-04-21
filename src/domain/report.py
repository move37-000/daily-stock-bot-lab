from dataclasses import dataclass
from datetime import date

from src.domain.market import ExchangeRate, MarketOverview
from src.domain.stock import StockSnapshot


@dataclass(frozen=True)
class DailyReport:
    """일일 주식 리포트 (알림·AI 분석·HTML 리포트 공통 입력)

    집계값(상승/하락 카운트, top gainer/loser 등)은 property로 계산한다.
    어댑터마다 집계 로직을 중복 구현하지 않도록 도메인이 제공한다.
    """
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
    def us_down_count(self) -> int:
        return len(self.us_stocks) - self.us_up_count

    @property
    def kr_up_count(self) -> int:
        return sum(1 for s in self.kr_stocks if s.is_up)

    @property
    def kr_down_count(self) -> int:
        return len(self.kr_stocks) - self.kr_up_count

    @property
    def top_gainer(self) -> StockSnapshot:
        return max(self.us_stocks + self.kr_stocks, key=lambda s: s.change_pct)

    @property
    def top_loser(self) -> StockSnapshot:
        return min(self.us_stocks + self.kr_stocks, key=lambda s: s.change_pct)