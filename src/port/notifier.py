from typing import Protocol

from src.domain.report import DailyReport


class Notifier(Protocol):
    """리포트 알림 전송 Port (Slack, Discord 등)

    어댑터는 DailyReport를 받아 플랫폼별 페이로드로 변환한 뒤 전송한다.
    상승/하락 카운트, top gainer/loser 같은 집계는 DailyReport의 property로
    이미 제공되므로 어댑터는 포맷팅과 전송에만 집중한다.

    webhook_url 등 플랫폼별 설정은 어댑터 생성자에서 주입받는다.
    report_url은 호출마다 달라지는 값이므로 메서드 인자로 유지한다.

    실패 시 예외를 발생시킨다. 재시도·스킵·중단 정책은 호출측
    (main.py)이 결정한다.
    """

    def send(self, report: DailyReport, report_url: str | None = None) -> None:
        ...