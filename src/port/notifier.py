from typing import Protocol
from src.domain.report import DailyReport

class Notifier(Protocol):
    def send(self, report: DailyReport, report_url: str | None = None) -> None:
        ...