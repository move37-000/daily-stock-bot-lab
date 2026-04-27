from src.domain.market import ExchangeRate, IndexSnapshot
from src.domain.report import DailyReport
from src.domain.stock import StockSnapshot


def build_prompt(report: DailyReport) -> str:
    """DailyReport를 Gemini 시황 분석용 프롬프트 문자열로 변환.

    AI 어댑터(GeminiAnalyzer 등)가 호출하는 순수 변환 함수. 외부 의존
    없음. AI 모델이 바뀌어도(Gemini → OpenAI 등) 같은 프롬프트를
    재사용할 수 있도록 어댑터에서 분리되어 있다.

    프롬프트 본문, 작성 규칙, 종목 요약 형식 등 AI 출력 품질에 영향을
    주는 모든 요소가 이 함수의 책임이다. 어댑터는 이 결과를 받아 API에
    전달하기만 한다.
    """
    sp500_line = _format_index(report.us_market.primary)
    nasdaq_line = _format_index(report.us_market.secondary)
    exchange_line = _format_exchange(report.exchange_rate)
    us_summary = _format_stock_summary(report.us_stocks, top_n=3)

    return f"""당신은 개인 투자자를 위한 주식 애널리스트입니다.
                아래 데이터를 바탕으로 오늘 한국장 개장 전 시황 브리핑을 작성해주세요.
                
                ## 데이터
                
                **미국장 (오늘 새벽 마감)**
                - S&P 500: {sp500_line}
                - NASDAQ: {nasdaq_line}
                - 환율 (USD/KRW): {exchange_line}
                - 주요 종목: {us_summary}
                
                ## 작성 규칙
                1. 7-8문장으로 간결하게
                2. 미국장 흐름 → 오늘 한국장 영향 전망 순서로
                3. 세계 정세나 주요 뉴스가 시장에 미치는 영향을 함께 설명
                4. 반말로 친근하게 ("~했어", "~될 것 같아")
                5. 숫자는 이미 위에 있으니 반복하지 말고 흐름 위주로
                6. 투자 권유가 아닌 정보 제공 목적
                
                브리핑을 작성해줘."""


def _format_index(index: IndexSnapshot) -> str:
    """지수 한 줄 포맷. '5,234.12 (+1.24%)' 형식."""
    return f"{index.formatted_price} ({index.formatted_change_pct}%)"