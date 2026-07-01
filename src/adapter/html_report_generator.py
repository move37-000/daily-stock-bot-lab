"""HTML 리포트 생성 어댑터.

DailyReport(도메인)를 받아 Jinja2 템플릿으로 HTML 파일을 만든다.

설계 결정 (Phase 5):
- Port를 두지 않는다. HTML 렌더러는 구현이 하나뿐이고 교체 가능성이 실재하지
    않아(§7.10) 모듈 함수로 노출한다. Notifier/MarketAnalyzer가 Port인 것과의
    비대칭은 "Port는 교체 가능성이 실재할 때만"의 사례다.
- 도메인 → 템플릿 변환은 이 모듈의 뷰모델(dict)로 격리한다. dict가 전 계층을
    흐르던 원본과 달리, 이 dict는 build_view_model 밖으로 나가지 않는다.
"""
import dataclasses

from src.config import LOGO_API_TOKEN, LOGO_API_URL, US_STOCK_DOMAINS
from src.domain.market import ExchangeRate, IndexSnapshot, MarketOverview
from src.domain.report import DailyReport
from src.domain.stock import StockSnapshot


def _logo_url(symbol: str) -> str:
    """symbol → logo.dev URL. 매핑에 없으면 빈 문자열(템플릿 onerror가 폴백)."""
    domain = US_STOCK_DOMAINS.get(symbol)
    if not domain:
        return ""
    return LOGO_API_URL.format(domain=domain, token=LOGO_API_TOKEN)


def _index_view(index: IndexSnapshot) -> dict:
    return {
        "price": index.formatted_price,
        "change": index.change,
        "change_pct": index.formatted_change_pct,
        "history": [dataclasses.asdict(p) for p in index.history],
    }