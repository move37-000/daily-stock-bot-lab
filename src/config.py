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