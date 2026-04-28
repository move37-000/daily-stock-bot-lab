from typing import Protocol

from src.domain.report import DailyReport


class MarketAnalyzer(Protocol):
    """AI 기반 시황 분석 Port

    DailyReport를 입력으로 받아 자연어 브리핑 문자열을 생성한다.
    Notifier와 동일하게 DailyReport를 공용 입력으로 사용하여 리포트·알림·
    AI 분석이 동일한 도메인 객체를 공유한다.

    프롬프트 조립은 어댑터 책임이 아니다. 서비스 레이어의 프롬프트
    빌더 함수에 분리되어 있으며, 어댑터는 완성된 프롬프트를 LLM에
    전달하고 응답을 반환하는 역할만 담당한다.

    API 키·모델 리스트 등 환경 설정은 어댑터 생성자에서 주입받는다.
    실패 시 예외를 발생시킨다 (성공 시 반드시 str 반환). API 키가 없는
    환경에서는 main.py가 어댑터 자체를 생성하지 않는다.
    """

    def analyze(self, report: DailyReport) -> str:
        ...