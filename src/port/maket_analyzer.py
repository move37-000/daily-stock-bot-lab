from typing import Protocol

from src.domain.report import DailyReport


class MarketAnalyzer(Protocol):
    def analyze(self, report: DailyReport) -> str:
        ...