from src.domain.report import DailyReport
from src.port.notifier import Notifier


class SlackNotifier(Notifier):
    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url

    def send(self, report: DailyReport, report_url: str | None = None) -> None:
        raise NotImplementedError  # Adapter 단계에서 구현