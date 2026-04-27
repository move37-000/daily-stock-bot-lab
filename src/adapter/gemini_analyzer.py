import logging

from google import genai

from src.adapter.prompt_builder import build_prompt
from src.domain.report import DailyReport
from src.port.market_analyzer import MarketAnalyzer

logger = logging.getLogger(__name__)