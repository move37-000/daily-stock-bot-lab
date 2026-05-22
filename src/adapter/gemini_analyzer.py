import logging

from google import genai

from src.adapter.prompt_builder import build_prompt
from src.domain.report import DailyReport
from src.port.market_analyzer import MarketAnalyzer

logger = logging.getLogger(__name__)


class GeminiAnalyzer(MarketAnalyzer):
    """Google Gemini 기반 시황 분석 어댑터.

    DailyReport를 프롬프트로 변환해 Gemini API에 전달하고 분석 텍스트를
    반환한다. 모델 폴백 체인을 내부에 품으며, 첫 번째 모델부터 순차 시도해
    성공한 결과를 즉시 반환한다.

    프롬프트 빌드 책임은 prompt_builder로 분리되어 있다. 이 어댑터는
    "Gemini API와의 상호작용"만 담당한다.

    다른 어댑터들은 raw 예외를 NetworkError/ParseError/ApiResponseError로 번역하지만,
    이 어댑터는 google.genai SDK 예외 계층을 번역하지 않는다.
    SDK 예외 구조를 모르기 때문.

    응답 본문이 None인 경우(safety filter 차단 등) ParseError로 즉시 발생.
    모든 모델 실패 시 AdapterError(루트) 전파.

    @retry는 달지 않는다. for model 루프가 이미 모델 단위 재시도 역할을
    하며, @retry를 단일 호출에 거는 건 폴백 체인과 이중 재시도로 겹친다.
    """

    def __init__(self, api_key: str, models: list[str]) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 존재하지 않음.")
        if not models:
            raise ValueError("models 리스트가 존재하지 않음.")
        self._api_key = api_key
        self._models = models

    def analyze(self, report: DailyReport) -> str:
        client = genai.Client(api_key=self._api_key)
        prompt = build_prompt(report)
        errors: list[tuple[str, Exception]] = []

        for model in self._models:
            try:
                logger.info(f"Gemini 모델 시도: {model}")
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                text = response.text
                if text is None:
                    # 응답 차단(safety filter 등) — 식별 가능하므로 명시 검증.
                    raise ParseError(f"Gemini 응답 본문이 비어있음 (model={model})")
                logger.info(f"Gemini 분석 성공: {model}")
                return text.strip()
            except Exception as e:
                # 의도적 광역 캐치
                errors.append((model, e))
                logger.warning(f"{model} 실패: {e}")

        raise AdapterError(f"모든 Gemini 모델 실패: {errors}")