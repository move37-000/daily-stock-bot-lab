import logging

import pandas as pd
import yfinance as yf

from src.domain.market import IndexSnapshot
from src.domain.stock import DailyPrice
from src.port.index_fetcher import IndexFetcher

logger = logging.getLogger(__name__)

class YFinanceIndexFetcher(IndexFetcher):
    """yfinance 기반 시장 지수 어댑터.

    S&P 500, NASDAQ 등 미국 지수 조회를 담당한다. 한국 지수(KOSPI, KOSDAQ)는
    Phase 7에서 KRX API 기반 어댑터로 별도 구현 예정 (STRUCTURE §7.5).

    데이터 부족(히스토리 2일 미만) 또는 조회 실패 시 RuntimeError를 던진다.
    실패를 기본값으로 위장하지 않는다 (§6.16 실패는 예외 원칙).
    """