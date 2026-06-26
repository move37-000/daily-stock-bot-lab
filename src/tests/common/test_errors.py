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


class TestApiResponseErrorFields:
    """ApiResponseError만 생성자가 다르다 (status_code, response_body)."""

    def test_status_code_저장(self):
        err = ApiResponseError("rate limited", status_code=429)
        assert err.status_code == 429

    def test_response_body_저장(self):
        err = ApiResponseError("bad", status_code=400, response_body="invalid input")
        assert err.response_body == "invalid input"

    def test_response_body_기본값_빈문자열(self):
        err = ApiResponseError("server error", status_code=500)
        assert err.response_body == ""

    def test_response_body_200자_초과시_절삭(self):
        """경계: response_body는 200자로 자른다.

        로그 폭주 방지가 의도. retry.py의 _is_retryable이 이걸 보지 않으니
        절삭으로 의미가 손실되진 않는다.
        """
        long_body = "x" * 500
        err = ApiResponseError("oversize", status_code=500, response_body=long_body)
        assert len(err.response_body) == 200
        assert err.response_body == "x" * 200

    def test_message는_str_으로_접근(self):
        """super().__init__(message)로 전달된 메시지가 str()로 노출."""
        err = ApiResponseError("not found", status_code=404)
        assert str(err) == "not found"


class TestExceptionChaining:
    """raise ... from ... 으로 원인 예외가 __cause__에 보존된다."""

    def test_raise_from_원인_보존(self):
        """어댑터가 외부 예외를 잡아 AdapterError로 번역할 때의 패턴.

        디버깅 시 원래 예외(yfinance.Exception 등)를 잃지 않게 한다.
        """
        original = ValueError("original cause")
        try:
            try:
                raise original
            except ValueError as e:
                raise NetworkError("translated") from e
        except NetworkError as e:
            assert e.__cause__ is original