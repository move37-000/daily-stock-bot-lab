"""date_utils 모듈 단위 테스트.

원본 tests/test_date_utils.py를 그대로 이식했다. 함수가 utils/에서 common/으로
모듈만 이동했을 뿐 동작은 동일하므로, 커버리지가 완성된 기존 테스트를 재사용한다.
import 경로(src.utils → src.common)만 수정.

Phase 4 결정 §원본 tests/ 처리: 살릴 거 / 버릴 거 분류 중 "살림"에 해당.
"""
from datetime import datetime

from src.common.date_utils import (
    _format_korean_time,
    format_kr_news_time,
    format_us_news_time,
)


class TestFormatUsNewsTime:
    """ISO 8601 → 한글 시간 포맷."""

    def test_빈_문자열(self):
        assert format_us_news_time("") == ""

    def test_정상_변환_오전(self):
        result = format_us_news_time("2024-03-18T09:30:00Z")
        assert "3월 18일" in result
        assert "오전" in result
        assert "9시 30분" in result

    def test_정상_변환_오후(self):
        result = format_us_news_time("2024-03-18T14:30:00Z")
        assert "3월 18일" in result
        assert "오후" in result
        assert "2시 30분" in result

    def test_자정(self):
        """자정(00시)은 오전 12시로 표시."""
        result = format_us_news_time("2024-03-18T00:00:00Z")
        assert "오전" in result
        assert "12시" in result

    def test_정오(self):
        """정오(12시)는 오후 12시로 표시."""
        result = format_us_news_time("2024-03-18T12:00:00Z")
        assert "오후" in result
        assert "12시" in result

    def test_잘못된_포맷(self):
        """파싱 실패 시 빈 문자열 (예외 던지지 않음)."""
        assert format_us_news_time("invalid-date") == ""


class TestFormatKrNewsTime:
    """네이버 형식 (YYYYMMDDHHMM) → 한글 시간 포맷."""

    def test_빈_문자열(self):
        assert format_kr_news_time("") == ""

    def test_짧은_문자열(self):
        """12자 미만은 빈 문자열."""
        assert format_kr_news_time("20240318") == ""

    def test_정상_변환_오전(self):
        result = format_kr_news_time("202403180930")
        assert "3월 18일" in result
        assert "오전" in result
        assert "9시 30분" in result

    def test_정상_변환_오후(self):
        result = format_kr_news_time("202403181430")
        assert "3월 18일" in result
        assert "오후" in result
        assert "2시 30분" in result


class TestFormatKoreanTime:
    """내부 헬퍼: datetime → 한글 포맷 문자열."""

    def test_오전(self):
        dt = datetime(2024, 3, 18, 9, 30)
        assert _format_korean_time(dt) == "3월 18일 오전 9시 30분"

    def test_오후(self):
        dt = datetime(2024, 3, 18, 15, 45)
        assert _format_korean_time(dt) == "3월 18일 오후 3시 45분"

    def test_자정(self):
        dt = datetime(2024, 3, 18, 0, 0)
        assert _format_korean_time(dt) == "3월 18일 오전 12시 0분"

    def test_정오(self):
        dt = datetime(2024, 3, 18, 12, 0)
        assert _format_korean_time(dt) == "3월 18일 오후 12시 0분"