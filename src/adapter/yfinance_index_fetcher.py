import logging

import requests
import yfinance as yf

from src.adapter._yfinance_common import (
    calculate_change,
    has_nan_close,
    parse_price_history,
    safe_history_metadata,
)
from src.common.diagnostics import dump_nan_incident
from src.common.errors import NetworkError, ParseError
from src.common.retry import retry
from src.domain.market import IndexSnapshot
from src.port.index_fetcher import IndexFetcher

logger = logging.getLogger(__name__)


class YFinanceIndexFetcher(IndexFetcher):
    """yfinance 기반 시장 지수 어댑터.

    S&P 500, NASDAQ 등 미국 지수 조회를 담당한다.

    조회 실패는 NetworkError, 데이터 부족(2일 미만)·파싱 실패는 ParseError로
    번역한다. 실패를 기본값으로 위장하지 않는다.

    @retry는 NetworkError / 5xx만 흡수한다. 데이터 부족은 재시도해도 같은
    결과이므로 ParseError로 분류해 즉시 실패시킨다.
    """

    _BUFFER_DAYS = 2  # 주말/공휴일로 인한 거래일 부족 커버용 버퍼

    def __init__(self, history_days: int = 5) -> None:
        self._history_days = history_days

    @retry(max_attempts=3, delay=2.0)
    def fetch(self, symbol: str, name: str) -> IndexSnapshot:
        period = f"{self._history_days + self._BUFFER_DAYS}d"
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period=period)
        except requests.RequestException as e:
            raise NetworkError(f"yfinance 연결 실패 ({name}, {symbol})") from e

        if len(history) < 2:
            # 데이터 부족은 재시도해도 같은 결과 → ParseError로 즉시 실패.
            raise ParseError(
                f"{name} ({symbol}) 지수 데이터 부족: {len(history)}일치"
            )

        # record-only (§종목 어댑터와 동일). tail() 전에 검사해 버퍼 구간까지 덤프에 남긴다.
        # 지수는 아직 NaN 사고가 난 적 없지만 같은 구멍이 있어 함께 계측한다.
        if has_nan_close(history):
            dump_path = dump_nan_incident(
                source="index",
                symbol=symbol,
                period=period,
                history=history,
                extra=safe_history_metadata(ticker),
            )
            logger.warning(f"NaN 종가 감지 ({name}, {symbol}) — 덤프: {dump_path}")

        try:
            history = history.tail(self._history_days)
            close, change, change_pct = calculate_change(history)
            price_points = parse_price_history(history)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            raise ParseError(f"yfinance 응답 파싱 실패 ({name}, {symbol})") from e

        return IndexSnapshot(
            name=name,
            price=close,
            change=change,
            change_pct=change_pct,
            history=price_points,
        )