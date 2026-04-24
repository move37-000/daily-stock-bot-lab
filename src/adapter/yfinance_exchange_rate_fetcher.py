import yfinance as yf

from src.adapter._yfinance_common import calculate_change
from src.domain.market import ExchangeRate
from src.port.exchange_rate_fetcher import ExchangeRateFetcher