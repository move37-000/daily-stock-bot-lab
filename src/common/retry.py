"""재시도 데코레이터

일시적 실패(네트워크 끊김, 서버 5xx, Rate Limit)를 자동 재시도로 흡수한다.
common/errors.py는 "무슨 일이 일어났는가"라는 사실만 담고,
"그래서 재시도하는가"라는 정책은 여기 둔다.

이 시스템은 GitHub Actions에서 하루 한 번, 단일 프로세스로 돈다.
지수 백오프가 푸는 문제(다수 클라이언트의 thundering herd)가 존재하지 않는다.
(빠르게 N번 시도하고 안 되면 깔끔하게 죽기)
"""

import functools
import logging
import time
from typing import Callable, TypeVar

from src.common.errors import ApiResponseError, NetworkError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _is_retryable(exc: Exception) -> bool:
    """재시도해서 풀릴 가능성이 있는 실패인지 판정한다.

    - NetworkError: 연결 끊김 / 타임아웃 — 다음 시도엔 풀릴 수 있다.
    - ApiResponseError 5xx: 서버 일시 장애
    - ApiResponseError 429: 4xx지만 Rate Limit — 잠시 후 풀린다.
    - ParseError·그 외 4xx / 알 수 없는 예외: 재시도 무의미.
    """
    if isinstance(exc, NetworkError):
        return True
    if isinstance(exc, ApiResponseError):
        return exc.status_code == 429 or exc.status_code >= 500
    return False