import pandas as pd


def calculate_change(history: pd.DataFrame) -> tuple[float, float, float]:
    """yfinance history DataFrame에서 (최신 종가, 전일 대비 변동, 변동률%) 계산.

    종목·지수·환율 어댑터가 공유하는 순수 계산 로직. history는 최소 2일치
    데이터를 포함해야 하며, 호출측에서 len(history) >= 2를 보장해야 한다.
    """
    latest = history.iloc[-1]
    prev = history.iloc[-2]
    close = float(latest["Close"])
    prev_close = float(prev["Close"])
    change = close - prev_close
    change_pct = (change / prev_close) * 100
    return close, change, change_pct