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


def retry(
    max_attempts: int = 3,
    delay: float = 2.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """재시도 데코레이터.

    Args:
        max_attempts: 총 시도 횟수. 3이면 최초 1회 + 재시도 2회.
            1이면 재시도 없음(= 데코레이터를 안 단 것과 동작 동일)
        delay: 재시도 사이 고정 대기(초).

    재시도 가능한 예외(_is_retryable)만 재시도한다. 재시도 불가 예외는
    즉시 전파한다. 모든 시도가 실패하면 마지막 예외를 그대로 전파한다.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    is_last = attempt == max_attempts
                    if is_last or not _is_retryable(e):
                        raise
                    logger.warning(
                        f"{func.__name__} 실패 "
                        f"(시도 {attempt}/{max_attempts}): {e} "
                        f"— {delay}초 후 재시도"
                    )
                    time.sleep(delay)
            # 도달 불가: 루프는 return 또는 raise로만 빠져나간다.
            raise AssertionError("retry 루프 불변식 위반")

        return wrapper

    return decorator