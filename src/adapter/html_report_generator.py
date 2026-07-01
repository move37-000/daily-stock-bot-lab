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


def _exchange_view(rate: ExchangeRate) -> dict:
    return {
        "price": rate.formatted_price,
        "change": rate.change,
        "change_pct": rate.formatted_change_pct,
        "history": [dataclasses.asdict(p) for p in rate.history],
    }


def _stock_view(stock: StockSnapshot) -> dict:
    return {
        "symbol": stock.symbol,
        "name": stock.name,
        "price": stock.formatted_price,
        "change": stock.change,
        "change_pct": stock.formatted_change_pct,
        "logo": _logo_url(stock.symbol),
        # StockDaily(OHLCV) → 차트용 {date, price}로 정규화.
        # 지수/환율 history(PricePoint)는 이미 {date, price}라 asdict로 충분하나
        # 종목은 close를 price로 바꿔야 JS(d.price)가 읽는다.
        "history": [{"date": d.date, "price": d.close} for d in stock.history],
        "news": [dataclasses.asdict(n) for n in stock.news],
    }


def _market_view(market: MarketOverview) -> dict:
    """primary/secondary(도메인) → sp500/nasdaq(템플릿 키)로 매핑."""
    return {
        "sp500": _index_view(market.primary),
        "nasdaq": _index_view(market.secondary),
    }


def build_view_model(report: DailyReport) -> dict:
    """DailyReport → 템플릿 렌더링용 dict 트리.

    로그로 확정한 계약(us_market/us_stocks/us_market_news/usd_krw/ai_comment)에
    1:1 대응한다. analysis(=ai_comment)는 None일 수 있고 템플릿이 조건 렌더한다.
    """
    return {
        "us_market": _market_view(report.us_market),
        "us_stocks": [_stock_view(s) for s in report.us_stocks],
        "us_market_news": [dataclasses.asdict(n) for n in report.us_news],
        "usd_krw": _exchange_view(report.exchange_rate),
        "ai_comment": report.analysis,
    }