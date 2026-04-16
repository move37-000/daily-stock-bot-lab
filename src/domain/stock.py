from dataclasses import dataclass


@dataclass(frozen=True)
class DailyPrice:
    """하루치 OHLCV 시세 데이터

    시세 데이터는 본질적으로 불변이므로 frozen=True로 설정.
    date는 "YYYY-MM-DD" 형식의 ISO 8601 문자열.
    """
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int