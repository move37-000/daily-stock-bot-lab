import logging

import pandas as pd
import yfinance as yf

from src.adapter._yfinance_common import calculate_change, parse_yfinance_news
from src.domain.news import NewsItem
from src.domain.stock import DailyPrice, Market, StockSnapshot
from src.port.stock_fetcher import StockFetcher

logger = logging.getLogger(__name__)


class YFinanceFetcher(StockFetcher):
    """yfinance 기반 미국 주식 어댑터.

    주가(5일치 OHLCV)와 종목 뉴스를 함께 조회하여 StockSnapshot을 반환한다.
    뉴스 조회 실패는 어댑터 내부에서 격리되어 news=[]로 처리되며,
    종목 단위 조회 실패는 해당 종목만 스킵한다. 모든 종목이 실패하면
    RuntimeError를 던진다.
    """

    def __init__(self, news_limit: int = 3) -> None:
        self._news_limit = news_limit

    def fetch(self, tickers: dict[str, str]) -> list[StockSnapshot]:
        results: list[StockSnapshot] = []
        errors: list[tuple[str, Exception]] = []

        for symbol, name in tickers.items():
            try:
                snapshot = self._fetch_one(symbol, name)
                if snapshot is not None:
                    results.append(snapshot)
            except Exception as e:
                errors.append((symbol, e))
                logger.warning(f"미국 주식 조회 실패 ({symbol}): {e}")

        if not results and errors:
            raise RuntimeError(f"모든 미국 종목 조회 실패: {errors}")

        return results

    def _fetch_one(self, symbol: str, name: str) -> StockSnapshot | None:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="5d")

        if history.empty:
            logger.warning(f"미국 주식 데이터 없음: {symbol}")
            return None

        daily_prices = self._parse_history(history)
        close, change, change_pct = calculate_change(history)
        news = self._fetch_news_safely(ticker, symbol)

        return StockSnapshot(
            symbol=symbol,
            name=name,
            market=Market.US,
            close=close,
            change=change,
            change_pct=change_pct,
            history=daily_prices,
            news=news,
        )

    @staticmethod
    def _parse_history(history: pd.DataFrame) -> list[DailyPrice]:
        return [
            DailyPrice(
                date=date.strftime("%Y-%m-%d"),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
            )
            for date, row in history.iterrows()
        ]

    def _fetch_news_safely(self, ticker: yf.Ticker, symbol: str) -> list[NewsItem]:
        """뉴스 실패 격리 — StockFetcher Port 규약에 따라 news=[]로 복귀.

        파싱 로직은 _yfinance_common.parse_yfinance_news에 위임. 이 메서드는
        실패 격리 책임만 담당한다. 분리 이유: 격리 정책이 Port마다 다르기
        때문(StockFetcher는 종목 단위 격리, MarketNewsFetcher는 리포트 단위 격리).
        """
        try:
            return parse_yfinance_news(ticker, self._news_limit)
        except Exception as e:
            logger.warning(f"뉴스 조회 실패 ({symbol}): {e}")
            return []