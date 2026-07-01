"""뉴스 시간 문자열을 한글 포맷으로 변환하는 유틸.

파싱 실패는 예외 대신 빈 문자열을 반환한다 — 뉴스 시각은 보조 표시 정보라
하나 깨졌다고 리포트 전체를 죽일 이유가 없다. (fetch 단계의 ParseError와
달리 여기선 soft-fail이 맞다.)
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def format_us_news_time(pub_date: str) -> str:
    """ISO 8601(yfinance) → 한글 시간.

    예: "2024-03-24T14:30:00Z" → "3월 24일 오후 2시 30분". 파싱 실패 시 "".
    """
    if not pub_date:
        return ""
    try:
        dt = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ")
        return _format_korean_time(dt)
    except ValueError as e:
        logger.debug(f"미국 뉴스 시간 파싱 실패: {pub_date}, {e}")
        return ""


def _format_korean_time(dt: datetime) -> str:
    """datetime → "3월 24일 오후 2시 30분" 형식."""
    hour = dt.hour
    minute = dt.minute

    if hour < 12:
        ampm = "오전"
        display_hour = hour if hour != 0 else 12
    else:
        ampm = "오후"
        display_hour = hour - 12 if hour != 12 else 12

    return f"{dt.month}월 {dt.day}일 {ampm} {display_hour}시 {minute}분"