"""SlackNotifier 어댑터 단위 테스트.

검증 책임:
1. 생성자 — 빈 webhook_url 거부
2. 정상 전송 — POST 호출 + payload 구조
3. 예외 번역 — HTTPError → ApiResponseError, RequestException → NetworkError
4. report_url 조건부 button block 분기

메시지 텍스트 라인 자체는 검증하지 않는다. 포맷 변경이 일상이라 테스트 부담만
커진다. 외부 API 통신 책임과 정책 분기만 검증.
"""
import pytest
import requests

from src.adapter.slack_notifier import SlackNotifier
from src.common.errors import ApiResponseError, NetworkError


# ---------- 모듈 fixture ----------

@pytest.fixture
def make_http_error(mocker):
    """requests.HTTPError + response 속성 셋업 factory.

    어댑터가 e.response.status_code와 e.response.text를 읽어
    ApiResponseError로 번역하므로 둘 다 정확히 셋업해야 한다.
    """
    def _make(status_code: int, body: str = "") -> requests.HTTPError:
        response = mocker.MagicMock()
        response.status_code = status_code
        response.text = body
        return requests.HTTPError(response=response)
    return _make


@pytest.fixture
def mock_post_success(mocker):
    """requests.post mock — 정상 응답 (raise_for_status 통과)."""
    response = mocker.MagicMock()
    response.raise_for_status.return_value = None
    return mocker.patch(
        "src.adapter.slack_notifier.requests.post",
        return_value=response,
    )


# ---------- 테스트 ----------

class TestConstructor:
    def test_빈_webhook_url_ValueError(self):
        with pytest.raises(ValueError, match="Slack webhook_url"):
            SlackNotifier(webhook_url="")


class TestNormalSend:
    def test_정상_전송_None_반환(self, mock_post_success, sample_daily_report):
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/xxx")
        result = notifier.send(sample_daily_report)
        assert result is None

    def test_webhook_url에_POST_요청(self, mock_post_success, sample_daily_report):
        url = "https://hooks.slack.com/services/T/B/X"
        SlackNotifier(webhook_url=url).send(sample_daily_report)

        args, _ = mock_post_success.call_args
        assert args[0] == url

    def test_payload에_blocks와_text_포함(
        self, mock_post_success, sample_daily_report,
    ):
        """페이로드 구조의 최소 약속: text + blocks 키 존재.

        메시지 내용 검증이 아니라 "Slack API가 요구하는 구조"를 만족하는지만 본다.
        """
        SlackNotifier(webhook_url="https://x").send(sample_daily_report)

        _, kwargs = mock_post_success.call_args
        payload = kwargs["json"]
        assert "blocks" in payload
        assert "text" in payload


class TestExceptionTranslation:
    """외부 예외를 도메인 예외로 번역 (Slack의 책임)."""

    def test_HTTPError_4xx_ApiResponseError로_번역(
        self, mocker, make_http_error, sample_daily_report,
    ):
        response = mocker.MagicMock()
        response.raise_for_status.side_effect = make_http_error(400, "bad payload")
        mocker.patch(
            "src.adapter.slack_notifier.requests.post",
            return_value=response,
        )

        notifier = SlackNotifier(webhook_url="https://x")
        with pytest.raises(ApiResponseError) as exc_info:
            notifier.send(sample_daily_report)

        assert exc_info.value.status_code == 400
        assert exc_info.value.response_body == "bad payload"

    def test_HTTPError_5xx_ApiResponseError로_번역(
        self, mocker, make_http_error, sample_daily_report,
    ):
        """5xx도 동일 번역. _is_retryable이 status_code를 보고 재시도 판정.

        SlackNotifier 자체는 @retry(max_attempts=1)이라 재시도 안 함,
        하지만 호출측이 재시도 정책 결정할 수 있게 번역만 해두는 것.
        """
        response = mocker.MagicMock()
        response.raise_for_status.side_effect = make_http_error(503)
        mocker.patch(
            "src.adapter.slack_notifier.requests.post",
            return_value=response,
        )

        notifier = SlackNotifier(webhook_url="https://x")
        with pytest.raises(ApiResponseError) as exc_info:
            notifier.send(sample_daily_report)

        assert exc_info.value.status_code == 503

    def test_ConnectionError_NetworkError로_번역(
        self, mocker, sample_daily_report,
    ):
        mocker.patch(
            "src.adapter.slack_notifier.requests.post",
            side_effect=requests.ConnectionError("connection refused"),
        )

        notifier = SlackNotifier(webhook_url="https://x")
        with pytest.raises(NetworkError):
            notifier.send(sample_daily_report)

    def test_Timeout_NetworkError로_번역(self, mocker, sample_daily_report):
        """Timeout은 RequestException 하위라 같은 except 절에 잡힘."""
        mocker.patch(
            "src.adapter.slack_notifier.requests.post",
            side_effect=requests.Timeout("read timeout"),
        )

        notifier = SlackNotifier(webhook_url="https://x")
        with pytest.raises(NetworkError):
            notifier.send(sample_daily_report)


class TestReportUrlConditional:
    """report_url 유무에 따라 button block 추가/생략 (정책 분기)."""

    def test_report_url_없으면_button_없음(
        self, mock_post_success, sample_daily_report,
    ):
        SlackNotifier(webhook_url="https://x").send(
            sample_daily_report, report_url=None,
        )

        _, kwargs = mock_post_success.call_args
        types = [b["type"] for b in kwargs["json"]["blocks"]]
        assert "actions" not in types

    def test_report_url_있으면_button_추가(
        self, mock_post_success, sample_daily_report,
    ):
        SlackNotifier(webhook_url="https://x").send(
            sample_daily_report, report_url="https://report.example.com/2024-03-19",
        )

        _, kwargs = mock_post_success.call_args
        types = [b["type"] for b in kwargs["json"]["blocks"]]
        assert "actions" in types