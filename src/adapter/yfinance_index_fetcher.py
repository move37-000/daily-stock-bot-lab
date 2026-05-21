import logging

import pandas as pd
import yfinance as yf

from src.adapter._yfinance_common import calculate_change
from src.domain.market import PricePoint, IndexSnapshot
from src.port.index_fetcher import IndexFetcher

logger = logging.getLogger(__name__)

class YFinanceIndexFetcher(IndexFetcher):
    """yfinance 기반 시장 지수 어댑터.

    S&P 500, NASDAQ 등 미국 지수 조회를 담당한다.

    데이터 부족(히스토리 2일 미만) 또는 조회 실패 시 RuntimeError를 던진다.
    실패를 기본값으로 위장하지 않는다.

    @retry는 NetworkError / 5xx만 흡수한다. 데이터 부족(ParseError)은
    재시도해도 같은 결과이므로 즉시 실패.
    """

    _BUFFER_DAYS = 2  # 주말/공휴일로 인한 거래일 부족 커버용 버퍼

    def __init__(self, history_days: int = 5) -> None:
        self._history_days = history_days

    @retry(max_attempts=3, delay=2.0)
    def fetch(self, symbol: str, name: str) -> IndexSnapshot:
        try:
            ticker = yf.Ticker(symbol)
            period = f"{self._history_days + self._BUFFER_DAYS}d"
            history = ticker.history(period=period)
        except requests.RequestException as e:
            raise NetworkError(f"yfinance 연결 실패 ({name}, {symbol})") from e

        if len(history) < 2:
            # 데이터 부족은 yfinance 응답 구조의 문제
            # 재시도해도 같은 결과. ParseError로 분류해 @retry가 헛돌지 않게 한다.
            raise RuntimeError(
                f"{name} ({symbol}) 지수 데이터 부족: {len(history)}일치"
            )

        try:
            history = history.tail(self._history_days)
            close, change, change_pct = calculate_change(history)
            price_points = self._parse_history(history)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            raise ParseError(f"yfinance 응답 파싱 실패 ({name}, {symbol})") from e

        return IndexSnapshot(
            name=name,
            price=close,
            change=change,
            change_pct=change_pct,
            history=price_points,
        )

    @staticmethod
    def _parse_history(history: pd.DataFrame) -> list[PricePoint]:
        return [
            PricePoint(
                date=date.strftime("%Y-%m-%d"),
                price=float(row["Close"])
            )
            for date, row in history.iterrows()
        ]