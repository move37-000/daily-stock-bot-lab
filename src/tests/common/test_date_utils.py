"""date_utils 모듈 단위 테스트.

원본 tests/test_date_utils.py를 그대로 이식했다. 함수가 utils/에서 common/으로
모듈만 이동했을 뿐 동작은 동일하므로, 커버리지가 완성된 기존 테스트를 재사용한다.
import 경로(src.utils → src.common)만 수정.

Phase 4 결정 §원본 tests/ 처리: 살릴 거 / 버릴 거 분류 중 "살림"에 해당.
"""
from datetime import datetime

from src.common.date_utils import (
    _format_korean_time,
    format_kr_news_time,
    format_us_news_time,
)