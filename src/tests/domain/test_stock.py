"""StockSnapshot 도메인 단위 테스트.

외부 의존성 없는 순수 도메인. property 계산만 검증한다.

이 파일은 conftest.py 픽스처를 거의 사용하지 않는다. 각 테스트가 요구하는
필드값(change, market 등)이 모두 달라 픽스처 1개로 커버하기 어렵고,
도메인 객체 생성 비용이 무시 가능한 수준이라 헬퍼 함수가 더 가볍다.
픽스처는 "공유 가치가 큰 무거운 객체"에 어울린다.
"""
from src.domain.stock import Market, StockSnapshot


def _snapshot(
        *,
        market: Market = Market.US,
        close: float = 178.5,
        change: float = 2.3,
        change_pct: float = 1.31,
) -> StockSnapshot:
    """필드 일부만 바꿔서 StockSnapshot을 만드는 헬퍼.

    키워드 전용 인자(`*`)로 강제해 호출측에서 어떤 필드를 바꾸는지
    명시되도록 했다.
    """
    return StockSnapshot(
        symbol="AAPL",
        name="Apple",
        market=market,
        close=close,
        change=change,
        change_pct=change_pct,
    )