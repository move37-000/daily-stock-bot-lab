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