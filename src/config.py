import os

from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Secrets (환경 변수)
# =============================================================================
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =============================================================================
# GitHub Pages 설정
# =============================================================================
GITHUB_USERNAME = "move37-000"
REPO_NAME = "Daily-Stock-Bot"
REPORT_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/?v1=v"

# =============================================================================
# 데이터 수집 설정
# =============================================================================
HISTORY_DAYS = 5  # 히스토리 조회 일수
NEWS_LIMIT = 3    # 뉴스 조회 개수

# =============================================================================
# 미국 주식 설정(임시)
# =============================================================================
US_TICKERS: dict[str, str] = {
    "NVDA": "NVIDIA Corporation",
    "QQQ": "Invesco QQQ Trust",
    "SCHD": "Schwab US Dividend Equity ETF",
}

# =============================================================================
# 지수 / 환율 / 시장 뉴스 심볼
# =============================================================================
US_INDICES: dict[str, str] = {
    "^GSPC": "S&P 500",
    "^IXIC": "NASDAQ",
}

USD_KRW_SYMBOL = "USDKRW=X"
USD_KRW_PAIR = "USD/KRW"

US_MARKET_NEWS_SYMBOL = "^GSPC"  # S&P 500에 딸린 yfinance 뉴스 사용

# =============================================================================
# AI 설정
# =============================================================================
GEMINI_MODELS = [
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

# =============================================================================
# HTML 리포트용 (별도 작업에서 사용)
# =============================================================================
US_STOCK_DOMAINS: dict[str, str] = {
    "NVDA": "nvidia.com",
    "QQQ": "invesco.com",
    "SCHD": "schwab.com",
}

LOGO_API_TOKEN = "pk_X-1ZO13GSgeOoUrIuJ6GMQ"
LOGO_API_URL = "https://img.logo.dev/{domain}?token={token}&size=40&format=png"
TOSS_LOGO_URL = "https://thumb.tossinvest.com/image/resized/40x0/https%3A%2F%2Fstatic.toss.im%2Fpng-icons%2Fsecurities%2Ficn-sec-fill-{code}.png"
