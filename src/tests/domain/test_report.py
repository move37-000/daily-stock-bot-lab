"""DailyReport 도메인 단위 테스트.

us_stocks 리스트 기반 집계 property와 __post_init__ 불변식을 검증한다.

이 테스트는 conftest의 sample_daily_report 픽스처를 활용한다.
픽스처가 "상승 1(AAPL) / 하락 1(MSFT)" 구성이라 top_gainer/top_loser 분리
검증이 자연스럽게 가능하다.

특정 필드만 다른 케이스에는 dataclasses.replace를 사용한다.
DailyReport가 frozen=True 이므로 직접 수정 불가, replace로 새 인스턴스 생성.
"""
from dataclasses import replace

import pytest


class TestPostInit:
    """__post_init__ 불변식: 빈 us_stocks 거부."""

    def test_빈_us_stocks_ValueError(self, sample_daily_report):
        with pytest.raises(ValueError):
            replace(sample_daily_report, us_stocks=[])


class TestUpDownCount:
    """us_up_count + us_down_count == len(us_stocks)."""

    def test_us_up_count(self, sample_daily_report):
        # 픽스처: 상승 1(AAPL) + 하락 1(MSFT)
        assert sample_daily_report.us_up_count == 1

    def test_us_down_count(self, sample_daily_report):
        assert sample_daily_report.us_down_count == 1

    def test_카운트_합은_전체_종목수(self, sample_daily_report):
        """경계 검증: up + down은 항상 전체와 같다.

        is_up이 change>=0이라 0(보합)도 up으로 분류되므로
        "보합" 같은 제3카테고리가 없다 — 그 정책이 깨지지 않는지
        합산으로 보장.
        """
        total = sample_daily_report.us_up_count + sample_daily_report.us_down_count
        assert total == len(sample_daily_report.us_stocks)


class TestTopGainerLoser:
    """change_pct 최대/최소 종목 반환."""

    def test_top_gainer는_최대_변동률(self, sample_daily_report):
        # AAPL: +1.31, MSFT: -1.23 → AAPL
        assert sample_daily_report.top_gainer.symbol == "AAPL"

    def test_top_loser는_최소_변동률(self, sample_daily_report):
        assert sample_daily_report.top_loser.symbol == "MSFT"

    def test_단일_종목이면_gainer_loser_동일(
            self, sample_daily_report, sample_stock_snapshot,
    ):
        """경계 조건: 종목 1개면 top_gainer == top_loser.

        호출측이 이걸 알고 분리 렌더링 여부를 결정해야 한다는 신호.
        도메인은 예외 던지지 않고 같은 객체 반환.
        """
        single = replace(sample_daily_report, us_stocks=[sample_stock_snapshot])
        assert single.top_gainer is single.top_loser