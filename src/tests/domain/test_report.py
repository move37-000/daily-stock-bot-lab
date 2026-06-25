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