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