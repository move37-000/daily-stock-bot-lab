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

    return f"""넌 개인 투자자를 위한 반도체 섹터 애널리스트야.

    아래 데이터로 오늘 한국장 개장 전 시황 브리핑을 작성해.
    분석 대상은 대한민국 반도체 섹터(주요 종목: 삼성전자/SK하이닉스(메모리/HBM))야.

    ## 데이터

    **미국장 (오늘 새벽 마감)**
    - S&P 500: {sp500_line}
    - NASDAQ: {nasdaq_line}
    - USD/KRW: {exchange_line}

    **선행 신호 (전일 등락 및 방향은 이미 계산됨)**
    - 주요 종목: {us_summary}

    ** 종목 분석 개요 **
    - MU (마이크론): 삼전·하닉 메모리 피어, 상관 최상
    - NVDA: HBM 수요 → 특히 하닉에 직접
    - TSM: 반도체 업황 전반 벨웨더

    ## 분석 규칙
    1. 선행 신호를 근거로 오늘 대한민국 반도체 섹터(주요 종목: 삼성전자/SK하이닉스(메모리/HBM))의 방향을 추론해.
        특히 MU→메모리 전반, NVDA→하닉 HBM 사슬을 명시적으로 연결해.
    2. 환율은 이중성을 반드시 짚어. (원화 약세: 수출 채산성 +, 외국인 수급 압력 -)
    3. 신호가 서로 엇갈리면 "엇갈린다"고 솔직하게 써. 억지로 한 방향으로 몰지 마.
    4. 데이터에 없는 걸 지어내지 마. 특히 뉴스·지정학·최근 업황 서사는
        프롬프트에 명시된 수치 외에 끌어오지 마. 주어진 등락률과 환율만으로 추론해.
    5. 6-7문장. 미국장 흐름 → 선행 신호가 대한민국 반도체 섹터(주요 종목: 삼성전자/SK하이닉스(메모리/HBM))에 주는 함의 순서.
    6. 이미 나온 숫자는 반복하지 말고 흐름·방향 위주로.
    7. 반말로 친근하게. 투자 권유가 아닌 정보 제공.

    브리핑을 작성해."""


def _format_index(index: IndexSnapshot) -> str:
    """지수 한 줄 포맷. '5,234.12 (+1.24%)' 형식."""
    return f"{index.formatted_price} ({index.formatted_change_pct}%)"

def _format_exchange(rate: ExchangeRate) -> str:
    """환율 한 줄 포맷. '1,345.50 (+0.12%)' 형식."""
    return f"{rate.formatted_price} ({rate.formatted_change_pct}%)"


def _format_stock_summary(
    stocks: list[StockSnapshot], top_n: int = 3
) -> str:
    """종목 요약 포맷. config 순서대로 앞 top_n개를 'NVDA +5.23%, QQQ +1.45%' 형식으로.

    정렬 안 함. config의 종목 순서가 사용자 관심 순서라는 원본 가정을 계승.
    변동률 정렬로 바꾸려면 sorted(stocks, key=lambda s: abs(s.change_pct), reverse=True).
    """
    return ", ".join(
        f"{s.symbol} {s.change_pct:+.2f}%"
        for s in stocks[:top_n]
    )