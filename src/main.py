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