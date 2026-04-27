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

    실패 시 예외를 전파한다 (Notifier와 동일 정책). API 키 누락 또는
    빈 모델 리스트는 생성자에서 즉시 ValueError. 모든 모델 호출 실패 시
    RuntimeError. 호출측 (main.py)이 try/except로 처리하여 AI 분석
    실패가 리포트 본체 송출을 막지 않게 한다.
    """