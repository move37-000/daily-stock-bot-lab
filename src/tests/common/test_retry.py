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


class TestRetryableExceptions:
    """재시도 가능 예외는 재시도 후 성공 또는 마지막 예외 전파."""

    def test_NetworkError_재시도_후_성공(self, mocker):
        """1, 2회 실패하고 3회에 성공하는 시나리오."""
        mocker.patch("src.common.retry.time.sleep")
        inner = mocker.Mock(side_effect=[
            NetworkError("flaky 1"),
            NetworkError("flaky 2"),
            "ok",
        ])

        @retry(max_attempts=3, delay=2.0)
        def fn():
            return inner()

        assert fn() == "ok"
        assert inner.call_count == 3

    def test_NetworkError_전회_실패시_마지막_예외_전파(self, mocker):
        mocker.patch("src.common.retry.time.sleep")
        inner = mocker.Mock(side_effect=[
            NetworkError("attempt 1"),
            NetworkError("attempt 2"),
            NetworkError("attempt 3"),
        ])

        @retry(max_attempts=3, delay=2.0)
        def fn():
            return inner()

        with pytest.raises(NetworkError, match="attempt 3"):
            fn()
        assert inner.call_count == 3

    def test_ApiResponseError_5xx_재시도(self, mocker):
        mocker.patch("src.common.retry.time.sleep")
        inner = mocker.Mock(side_effect=[
            ApiResponseError("server down", status_code=503),
            "ok",
        ])

        @retry(max_attempts=3, delay=2.0)
        def fn():
            return inner()

        assert fn() == "ok"
        assert inner.call_count == 2

    def test_ApiResponseError_429_재시도(self, mocker):
        """4xx지만 Rate Limit은 재시도 가능."""
        mocker.patch("src.common.retry.time.sleep")
        inner = mocker.Mock(side_effect=[
            ApiResponseError("rate limited", status_code=429),
            "ok",
        ])

        @retry(max_attempts=3, delay=2.0)
        def fn():
            return inner()

        assert fn() == "ok"


class TestNonRetryableExceptions:
    """재시도 불가 예외는 즉시 전파 (재시도 안 함)."""

    def test_ParseError_즉시_전파(self, mocker):
        mock_sleep = mocker.patch("src.common.retry.time.sleep")
        inner = mocker.Mock(side_effect=ParseError("bad json"))

        @retry(max_attempts=3, delay=2.0)
        def fn():
            return inner()

        with pytest.raises(ParseError):
            fn()
        assert inner.call_count == 1  # 재시도 없음
        assert mock_sleep.call_count == 0

    def test_ApiResponseError_4xx_즉시_전파(self, mocker):
        """400 등 클라이언트 오류는 재시도 무의미."""
        mock_sleep = mocker.patch("src.common.retry.time.sleep")
        inner = mocker.Mock(side_effect=ApiResponseError("bad req", status_code=400))

        @retry(max_attempts=3, delay=2.0)
        def fn():
            return inner()

        with pytest.raises(ApiResponseError):
            fn()
        assert inner.call_count == 1
        assert mock_sleep.call_count == 0

    def test_알수없는_예외_즉시_전파(self, mocker):
        """_is_retryable이 False를 반환하는 모든 예외."""
        mock_sleep = mocker.patch("src.common.retry.time.sleep")
        inner = mocker.Mock(side_effect=ValueError("unexpected"))

        @retry(max_attempts=3, delay=2.0)
        def fn():
            return inner()

        with pytest.raises(ValueError):
            fn()
        assert inner.call_count == 1
        assert mock_sleep.call_count == 0


class TestSleepBehavior:
    """§7.7 핵심: time.sleep이 실제로 호출되는지 검증."""

    def test_재시도_사이_sleep_호출_횟수(self, mocker):
        """3회 시도하고 모두 재시도 가능 예외 → sleep 2회.

        마지막 실패 후엔 sleep 없이 raise (불필요한 대기 차단).
        """
        mock_sleep = mocker.patch("src.common.retry.time.sleep")

        @retry(max_attempts=3, delay=2.0)
        def fn():
            raise NetworkError("flaky")

        with pytest.raises(NetworkError):
            fn()
        assert mock_sleep.call_count == 2

    def test_sleep이_delay값으로_호출(self, mocker):
        """delay=1.5가 그대로 time.sleep에 전달되는지."""
        mock_sleep = mocker.patch("src.common.retry.time.sleep")

        @retry(max_attempts=2, delay=1.5)
        def fn():
            raise NetworkError("flaky")

        with pytest.raises(NetworkError):
            fn()
        mock_sleep.assert_called_once_with(1.5)


class TestBoundaryConditions:
    def test_max_attempts_1이면_재시도_없음(self, mocker):
        """경계: max_attempts=1은 데코레이터 미적용과 동작 동일.

        재시도 가능 예외라도 1회 시도 후 즉시 전파.
        """
        mock_sleep = mocker.patch("src.common.retry.time.sleep")
        inner = mocker.Mock(side_effect=NetworkError("once"))

        @retry(max_attempts=1, delay=2.0)
        def fn():
            return inner()

        with pytest.raises(NetworkError):
            fn()
        assert inner.call_count == 1
        assert mock_sleep.call_count == 0
