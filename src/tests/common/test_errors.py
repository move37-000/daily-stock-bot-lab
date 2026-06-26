"""common/errors 단위 테스트.

예외 계층(평면)과 ApiResponseError의 부가 필드를 검증한다.
"무슨 일이 일어났는가"만 담는 데이터 객체에 가깝다는 점에서 도메인
테스트와 성격이 유사하다 (외부 의존성 없음).
"""
import pytest

from src.common.errors import (
    AdapterError,
    ApiResponseError,
    NetworkError,
    ParseError,
)


class TestHierarchy:
    """모든 예외는 AdapterError로 잡힌다 (main.py의 단일 catch 보장)."""

    def test_NetworkError는_AdapterError(self):
        assert issubclass(NetworkError, AdapterError)

    def test_ParseError는_AdapterError(self):
        assert issubclass(ParseError, AdapterError)

    def test_ApiResponseError는_AdapterError(self):
        assert issubclass(ApiResponseError, AdapterError)

    def test_AdapterError로_하위_예외_catch_가능(self):
        """main.py가 except AdapterError 하나로 모두 잡는 게 가능한가."""
        with pytest.raises(AdapterError):
            raise NetworkError("connection refused")

        with pytest.raises(AdapterError):
            raise ParseError("missing key")

        with pytest.raises(AdapterError):
            raise ApiResponseError("4xx", status_code=400)