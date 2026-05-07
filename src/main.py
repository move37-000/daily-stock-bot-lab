import logging
import sys
from dataclasses import replace
from datetime import date

from src.adapter.discord_notifier import DiscordNotifier
from src.adapter.gemini_analyzer import GeminiAnalyzer
from src.adapter.slack_notifier import SlackNotifier
from src.adapter.yfinance_exchange_rate_fetcher import YFinanceExchangeRateFetcher
from src.adapter.yfinance_fetcher import YFinanceFetcher
from src.adapter.yfinance_index_fetcher import YFinanceIndexFetcher
from src.adapter.yfinance_market_news_fetcher import YFinanceMarketNewsFetcher
from src.config import (
    DISCORD_WEBHOOK_URL,
    GEMINI_API_KEY,
    GEMINI_MODELS,
    NEWS_LIMIT,
    REPORT_URL,
    SLACK_WEBHOOK_URL,
    US_INDICES,
    US_MARKET_NEWS_SYMBOL,
    US_TICKERS,
    USD_KRW_PAIR,
    USD_KRW_SYMBOL,
)
from src.domain.market import MarketOverview
from src.domain.report import DailyReport
from src.domain.stock import Market
from src.port.market_analyzer import MarketAnalyzer
from src.port.notifier import Notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    # =======================================================================
    # 1. 어댑터 인스턴스 생성 (DI 조립)
    # ======================================================================
    stock_fetcher = YFinanceFetcher(news_limit=NEWS_LIMIT)
    index_fetcher = YFinanceIndexFetcher()
    exchange_fetcher = YFinanceExchangeRateFetcher(
        symbol=USD_KRW_SYMBOL,
        pair=USD_KRW_PAIR,
    )
    news_fetcher = YFinanceMarketNewsFetcher(
        symbol=US_MARKET_NEWS_SYMBOL,
        news_limit=NEWS_LIMIT,
    )