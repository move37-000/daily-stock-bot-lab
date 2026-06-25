"""Phase 4 공용 픽스처 + Fake 어댑터.

도메인 객체 픽스처는 각 테스트에서 일부 필드만 바꿔 쓰기 좋게 최소 구성으로 둔다.
Fake 어댑터는 Port를 명시 구현해 헥사고날의 "테스트 가능성" 약속을 실물로 증명한다.
"""
from datetime import date

import pytest

from src.domain.market import ExchangeRate, IndexSnapshot, MarketOverview, PricePoint
from src.domain.news import NewsItem
from src.domain.report import DailyReport
from src.domain.stock import Market, StockDaily, StockSnapshot
from src.port.notifier import Notifier
from src.port.stock_fetcher import StockFetcher


@pytest.fixture
def sample_stock_daily() -> StockDaily:
    return StockDaily(
        date="2024-03-19",
        open=176.0,
        high=179.0,
        low=175.5,
        close=178.5,
        volume=1_000_000,
    )


@pytest.fixture
def sample_news_item() -> NewsItem:
    return NewsItem(
        title="Apple unveils new iPhone",
        link="https://news.example.com/apple",
        publisher="Reuters",
        time="3월 19일 오후 2시 30분",
    )


@pytest.fixture
def sample_stock_snapshot(sample_stock_daily, sample_news_item) -> StockSnapshot:
    return StockSnapshot(
        symbol="AAPL",
        name="Apple Inc.",
        market=Market.US,
        close=178.5,
        change=2.3,
        change_pct=1.31,
        history=[sample_stock_daily],
        news=[sample_news_item],
    )


@pytest.fixture
def sample_stock_snapshot_down() -> StockSnapshot:
    """change_pct 음수. top_loser 테스트용."""
    return StockSnapshot(
        symbol="MSFT",
        name="Microsoft",
        market=Market.US,
        close=400.0,
        change=-5.0,
        change_pct=-1.23,
    )


@pytest.fixture
def sample_index_snapshot() -> IndexSnapshot:
    return IndexSnapshot(
        name="S&P 500",
        price=5200.00,
        change=20.0,
        change_pct=0.39,
        history=[PricePoint(date="2024-03-19", price=5200.00)],
    )


@pytest.fixture
def sample_market_overview(sample_index_snapshot) -> MarketOverview:
    nasdaq = IndexSnapshot(
        name="NASDAQ",
        price=16000.0,
        change=50.0,
        change_pct=0.31,
    )
    return MarketOverview(
        market=Market.US,
        primary=sample_index_snapshot,
        secondary=nasdaq,
    )


@pytest.fixture
def sample_exchange_rate() -> ExchangeRate:
    return ExchangeRate(
        pair="USD/KRW",
        price=1340.50,
        change=-1.5,
        change_pct=-0.11,
    )


@pytest.fixture
def sample_daily_report(
    sample_stock_snapshot,
    sample_stock_snapshot_down,
    sample_market_overview,
    sample_exchange_rate,
    sample_news_item,
) -> DailyReport:
    """us_stocks 2개(상승 1 / 하락 1) 포함. top_gainer/top_loser 분리 검증 가능."""
    return DailyReport(
        date=date(2024, 3, 19),
        us_stocks=[sample_stock_snapshot, sample_stock_snapshot_down],
        us_market=sample_market_overview,
        exchange_rate=sample_exchange_rate,
        us_news=[sample_news_item],
    )


# ---------- Fake 어댑터 ----------


class FakeStockFetcher(StockFetcher):
    """StockFetcher Port의 테스트 전용 구현체.

    외부 I/O 없이 생성자에서 받은 스냅샷 리스트를 그대로 반환한다.
    Mock(`MagicMock(spec=StockFetcher)`)이 Port를 흉내내는 것과 달리,
    Fake는 Port를 명시 상속해 mypy가 계약 위반을 정적으로 잡는다.
    """

    def __init__(self, snapshots: list[StockSnapshot]) -> None:
        self._snapshots = snapshots
        self.fetch_calls: list[dict[str, str]] = []

    def fetch(self, tickers: dict[str, str]) -> list[StockSnapshot]:
        self.fetch_calls.append(tickers)
        return self._snapshots