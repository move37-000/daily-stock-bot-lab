"""DiscordNotifier 어댑터 단위 테스트.

Slack과 사실상 동형. 차이는 두 가지뿐:
1. payload 구조 — blocks 대신 embeds, report_url은 description 내 markdown 링크
2. 에러 메시지 prefix — "Discord ..."

예외 번역(HTTPError → ApiResponseError, RequestException → NetworkError)과
@retry(max_attempts=1) 정책은 Slack과 완전 동일.

NOTE: Slack과 테스트 패턴이 거의 같다. 다음 프로젝트에서는 parametrize 또는
공통 base 테스트 클래스로 중복 제거 검토 (회고 §7.11 후보).
"""
import pytest
import requests

from src.adapter.discord_notifier import DiscordNotifier
from src.common.errors import ApiResponseError, NetworkError


# ---------- 모듈 fixture ----------

@pytest.fixture
def make_http_error(mocker):
    def _make(status_code: int, body: str = "") -> requests.HTTPError:
        response = mocker.MagicMock()
        response.status_code = status_code
        response.text = body
        return requests.HTTPError(response=response)
    return _make


@pytest.fixture
def mock_post_success(mocker):
    response = mocker.MagicMock()
    response.raise_for_status.return_value = None
    return mocker.patch(
        "src.adapter.discord_notifier.requests.post",
        return_value=response,
    )


# ---------- 테스트 ----------

class TestConstructor:
    def test_빈_webhook_url_ValueError(self):
        with pytest.raises(ValueError, match="Discord webhook_url"):
            DiscordNotifier(webhook_url="")


class TestNormalSend:
    def test_정상_전송_None_반환(self, mock_post_success, sample_daily_report):
        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/x/y",
        )
        result = notifier.send(sample_daily_report)
        assert result is None

    def test_webhook_url에_POST_요청(self, mock_post_success, sample_daily_report):
        url = "https://discord.com/api/webhooks/123/abc"
        DiscordNotifier(webhook_url=url).send(sample_daily_report)

        args, _ = mock_post_success.call_args
        assert args[0] == url

    def test_payload에_embeds_포함(self, mock_post_success, sample_daily_report):
        """Discord API가 요구하는 구조: embeds 배열, 최소 1개 embed."""
        DiscordNotifier(webhook_url="https://x").send(sample_daily_report)

        _, kwargs = mock_post_success.call_args
        payload = kwargs["json"]
        assert "embeds" in payload
        assert len(payload["embeds"]) >= 1


class TestExceptionTranslation:
    """Slack과 동일한 번역 정책."""

    def test_HTTPError_4xx_ApiResponseError로_번역(
        self, mocker, make_http_error, sample_daily_report,
    ):
        response = mocker.MagicMock()
        response.raise_for_status.side_effect = make_http_error(400, "bad payload")
        mocker.patch(
            "src.adapter.discord_notifier.requests.post",
            return_value=response,
        )

        notifier = DiscordNotifier(webhook_url="https://x")
        with pytest.raises(ApiResponseError) as exc_info:
            notifier.send(sample_daily_report)

        assert exc_info.value.status_code == 400
        assert exc_info.value.response_body == "bad payload"

    def test_HTTPError_5xx_ApiResponseError로_번역(
        self, mocker, make_http_error, sample_daily_report,
    ):
        response = mocker.MagicMock()
        response.raise_for_status.side_effect = make_http_error(503)
        mocker.patch(
            "src.adapter.discord_notifier.requests.post",
            return_value=response,
        )

        notifier = DiscordNotifier(webhook_url="https://x")
        with pytest.raises(ApiResponseError) as exc_info:
            notifier.send(sample_daily_report)

        assert exc_info.value.status_code == 503

    def test_ConnectionError_NetworkError로_번역(
        self, mocker, sample_daily_report,
    ):
        mocker.patch(
            "src.adapter.discord_notifier.requests.post",
            side_effect=requests.ConnectionError("connection refused"),
        )

        notifier = DiscordNotifier(webhook_url="https://x")
        with pytest.raises(NetworkError):
            notifier.send(sample_daily_report)

    def test_Timeout_NetworkError로_번역(self, mocker, sample_daily_report):
        mocker.patch(
            "src.adapter.discord_notifier.requests.post",
            side_effect=requests.Timeout("read timeout"),
        )

        notifier = DiscordNotifier(webhook_url="https://x")
        with pytest.raises(NetworkError):
            notifier.send(sample_daily_report)


class TestReportUrlConditional:
    """report_url 유무에 따라 description 내 markdown 링크 추가/생략.

    Slack은 별도 button block을 추가하지만 Discord는 description 텍스트에
    markdown 링크를 끼워넣는 방식. payload 구조 자체는 안 변함.
    """

    def test_report_url_있으면_description에_링크(
        self, mock_post_success, sample_daily_report,
    ):
        report_url = "https://report.example.com/2024-03-19"
        DiscordNotifier(webhook_url="https://x").send(
            sample_daily_report, report_url=report_url,
        )

        _, kwargs = mock_post_success.call_args
        description = kwargs["json"]["embeds"][0]["description"]
        assert report_url in description

    def test_report_url_없으면_링크_텍스트_없음(
        self, mock_post_success, sample_daily_report,
    ):
        DiscordNotifier(webhook_url="https://x").send(
            sample_daily_report, report_url=None,
        )

        _, kwargs = mock_post_success.call_args
        description = kwargs["json"]["embeds"][0]["description"]
        assert "전체 리포트 보기" not in description