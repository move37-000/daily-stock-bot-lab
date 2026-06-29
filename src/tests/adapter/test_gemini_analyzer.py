"""GeminiAnalyzer 어댑터 단위 테스트.

검증 책임:
1. 생성자 검증 (빈 api_key, 빈 models)
2. 정상 경로 — 첫 모델 성공
3. 폴백 체인 — 모델 N개를 순서대로 시도, 첫 성공한 결과 반환
4. safety filter 차단 (text=None) → ParseError → for문이 catch → 다음 모델
5. 모든 모델 실패 → AdapterError 전파

prompt_builder는 mock한다. build_prompt 자체 테스트는 별도 파일에 있어야 하나
현재 누락 — 회고 항목.

테스트가 늘면 mock 셋업 반복이 부담이라 fixture로 묶었다 (mock_client, make_response).
"""
import pytest

from src.adapter.gemini_analyzer import GeminiAnalyzer
from src.common.errors import AdapterError


# ---------- 모듈 fixture ----------

@pytest.fixture
def make_response(mocker):
    """Gemini API 응답 mock factory.

    factory fixture 패턴: fixture가 객체가 아니라 "객체 만드는 함수"를 반환.
    각 테스트가 response.text 값만 호출 인자로 다르게 줄 수 있다.
    """
    def _make(text: str | None) -> object:
        r = mocker.MagicMock()
        r.text = text
        return r
    return _make


@pytest.fixture
def mock_client(mocker):
    """genai.Client + build_prompt를 미리 patch.

    이 fixture를 요청한 테스트는 client.models.generate_content의
    side_effect/return_value만 설정하면 된다. fixture는 mock client를 반환.
    """
    client = mocker.MagicMock()
    mocker.patch(
        "src.adapter.gemini_analyzer.genai.Client",
        return_value=client,
    )
    mocker.patch(
        "src.adapter.gemini_analyzer.build_prompt",
        return_value="test prompt",
    )
    return client


# ---------- 테스트 ----------

class TestConstructor:
    """fail-fast: 빈 인자는 생성 시점에 거부."""

    def test_빈_api_key_ValueError(self):
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiAnalyzer(api_key="", models=["gemini-2.0"])

    def test_빈_models_리스트_ValueError(self):
        with pytest.raises(ValueError, match="models"):
            GeminiAnalyzer(api_key="test-key", models=[])


class TestNormalPath:
    def test_첫_모델_성공시_결과_strip되어_반환(
        self, mock_client, make_response, sample_daily_report,
    ):
        """text.strip() 적용 확인 — 앞뒤 공백/개행 제거."""
        mock_client.models.generate_content.return_value = make_response(
            "  분석 결과 텍스트\n"
        )

        analyzer = GeminiAnalyzer(api_key="k", models=["gemini-2.0"])
        result = analyzer.analyze(sample_daily_report)

        assert result == "분석 결과 텍스트"
        assert mock_client.models.generate_content.call_count == 1


class TestFallbackChain:
    """모델 폴백: 순서대로 시도, 첫 성공한 결과 반환, 이후 모델은 호출 안 함."""

    def test_첫_실패_두번째_성공(
        self, mock_client, make_response, sample_daily_report,
    ):
        mock_client.models.generate_content.side_effect = [
            Exception("model 1 unavailable"),
            make_response("success from m2"),
        ]

        analyzer = GeminiAnalyzer(api_key="k", models=["m1", "m2"])
        result = analyzer.analyze(sample_daily_report)

        assert result == "success from m2"
        assert mock_client.models.generate_content.call_count == 2

    def test_모델_순서대로_호출(
        self, mock_client, make_response, sample_daily_report,
    ):
        """폴백이 models 리스트의 인덱스 순서를 따르는가.

        리스트 순서 = 우선순위. m1이 1순위, m3이 마지막 폴백.
        """
        mock_client.models.generate_content.side_effect = [
            Exception("m1 fail"),
            Exception("m2 fail"),
            make_response("ok from m3"),
        ]

        analyzer = GeminiAnalyzer(api_key="k", models=["m1", "m2", "m3"])
        analyzer.analyze(sample_daily_report)

        calls = mock_client.models.generate_content.call_args_list
        assert calls[0].kwargs["model"] == "m1"
        assert calls[1].kwargs["model"] == "m2"
        assert calls[2].kwargs["model"] == "m3"

    def test_성공_이후_모델은_호출_안_함(
        self, mock_client, make_response, sample_daily_report,
    ):
        """첫 성공 즉시 반환 — 나머지 폴백 호출 안 함 (불필요한 API 호출 차단)."""
        mock_client.models.generate_content.side_effect = [
            make_response("ok from m1"),
            make_response("should not be called"),
        ]

        analyzer = GeminiAnalyzer(api_key="k", models=["m1", "m2"])
        result = analyzer.analyze(sample_daily_report)

        assert result == "ok from m1"
        assert mock_client.models.generate_content.call_count == 1


class TestSafetyFilterBlock:
    """safety filter 차단 등으로 response.text가 None인 경우."""

    def test_text_None시_ParseError_후_다음_모델_시도(
        self, mock_client, make_response, sample_daily_report,
    ):
        """text=None → ParseError raise → for문이 catch → 폴백.

        Gemini API는 safety 정책 위반 시 200 OK이면서 text=None을 보낸다.
        다른 모델은 정책이 다를 수 있어 폴백 의미가 있다.
        """
        mock_client.models.generate_content.side_effect = [
            make_response(None),                  # m1 차단
            make_response("ok from m2"),          # m2 통과
        ]

        analyzer = GeminiAnalyzer(api_key="k", models=["m1", "m2"])
        result = analyzer.analyze(sample_daily_report)

        assert result == "ok from m2"
        assert mock_client.models.generate_content.call_count == 2

    def test_전모델_차단시_AdapterError(
        self, mock_client, make_response, sample_daily_report,
    ):
        """경계: 모든 모델이 safety filter에 막혀도 AdapterError로 통합 표면화."""
        mock_client.models.generate_content.side_effect = [
            make_response(None),
            make_response(None),
        ]

        analyzer = GeminiAnalyzer(api_key="k", models=["m1", "m2"])

        with pytest.raises(AdapterError, match="모든 Gemini 모델 실패"):
            analyzer.analyze(sample_daily_report)


class TestAllModelsFail:
    def test_전모델_예외_발생시_AdapterError(
        self, mock_client, sample_daily_report,
    ):
        """모든 모델이 예외 → AdapterError로 통합 raise.

        개별 모델 예외 정보는 errors 리스트에 누적되어 메시지에 포함.
        호출측(main.py)이 그 메시지로 어떤 모델이 어떻게 실패했는지 로그 확인 가능.
        """
        mock_client.models.generate_content.side_effect = [
            Exception("m1 quota exceeded"),
            Exception("m2 timeout"),
        ]

        analyzer = GeminiAnalyzer(api_key="k", models=["m1", "m2"])

        with pytest.raises(AdapterError, match="모든 Gemini 모델 실패"):
            analyzer.analyze(sample_daily_report)