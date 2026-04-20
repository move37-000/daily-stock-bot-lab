from src.domain.report import DailyReport
from src.port.market_analyzer import MarketAnalyzer


class GeminiAnalyzer(MarketAnalyzer):
    def __init__(self, api_key: str, models: list[str]):
        self._api_key = api_key
        self._models = models

    def analyze(self, report: DailyReport) -> str:
        raise NotImplementedError  # Adapter 단계에서 구현