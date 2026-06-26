"""@retry 데코레이터 단위 테스트.

핵심 검증 포인트:
1. 재시도 가능 예외(NetworkError, 5xx, 429)만 재시도하고 그 외는 즉시 전파
2. 모든 시도가 실패하면 마지막 예외 전파
3. 시도 사이에 실제로 time.sleep이 호출됨

§7.7 결정: time.sleep을 mocker.patch로 가로채는 방식 채택.
- delay=0으로 우회하는 방법은 sleep 호출 자체를 검증하지 못함.
- sleep_fn을 파라미터로 주입하는 방법은 현재 사용처가 없어 YAGNI.
patch 경로는 src.common.retry.time.sleep — "정의된 곳(time 모듈)"이 아니라
"사용되는 곳(retry 모듈이 import한 time)"을 잡아야 효과가 있다.
"""
import pytest

from src.common.errors import ApiResponseError, NetworkError, ParseError
from src.common.retry import retry


class TestSuccessPath:
    def test_성공시_즉시_반환(self, mocker):
        """1회 시도로 성공하면 그대로 반환. sleep 호출 안 됨."""
        mock_sleep = mocker.patch("src.common.retry.time.sleep")

        @retry(max_attempts=3, delay=2.0)
        def fn():
            return "ok"

        assert fn() == "ok"
        assert mock_sleep.call_count == 0