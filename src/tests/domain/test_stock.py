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


class TestIsUp:
    """is_up: change >= 0 → True (경계 조건 0 포함)."""

    def test_양수_상승(self):
        assert _snapshot(change=2.3).is_up is True

    def test_zero_상승_취급(self):
        """경계 조건: 변동 0은 상승으로 분류.

        하락 카운트에 포함되지 않게 하기 위한 정책 결정.
        """
        assert _snapshot(change=0.0).is_up is True

    def test_음수_하락(self):
        assert _snapshot(change=-1.5).is_up is False


class TestFormattedPrice:
    """KR은 정수+콤마, US는 소수점 2자리+콤마."""

    def test_US_소수점_2자리(self):
        assert _snapshot(market=Market.US, close=178.5).formatted_price == "178.50"

    def test_US_천단위_콤마(self):
        assert _snapshot(market=Market.US, close=5234.567).formatted_price == "5,234.57"

    def test_KR_정수_콤마(self):
        assert _snapshot(market=Market.KR, close=71_500.0).formatted_price == "71,500"


class TestEmoji:
    def test_상승_초록(self):
        assert _snapshot(change=1.0).emoji == "🟢"

    def test_하락_빨강(self):
        assert _snapshot(change=-1.0).emoji == "🔴"


class TestFormattedChangePct:
    """부호 포함 + 소수점 2자리 (예: '+1.73', '-0.45')."""

    def test_양수_플러스_부호(self):
        assert _snapshot(change_pct=1.731).formatted_change_pct == "+1.73"

    def test_음수_마이너스_부호(self):
        assert _snapshot(change_pct=-0.451).formatted_change_pct == "-0.45"

    def test_zero_플러스_부호(self):
        """경계: 0도 부호 +를 붙인다 (f-string `:+.2f` 동작)."""
        assert _snapshot(change_pct=0.0).formatted_change_pct == "+0.00"