import logging

import pandas as pd
import yfinance as yf

from src.domain.market import IndexSnapshot
from src.domain.stock import DailyPrice
from src.port.index_fetcher import IndexFetcher

logger = logging.getLogger(__name__)