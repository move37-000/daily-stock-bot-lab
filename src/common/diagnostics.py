"""NaN 사고 증거 덤프.

야후가 간헐적으로(실측 약 5%) 마지막 거래일 종가를 null로 내려보내는 일이 있다.
발생 자체는 상류 문제라 막을 수 없지만, 지금까지는 사고가 나도 렌더링된 HTML 하나만
남아서 원인을 추측할 근거가 없었다. 이 모듈은 그 순간의 원본 데이터를 파일로 남긴다.

record-only 도구다. 감지해도 파이프라인을 막지 않으며, **어떤 경우에도 예외를 던지지
않는다**. 진단 도구가 본체를 죽이면 본말전도이므로 전부 삼키고 경고만 남긴다
(_yfinance_common의 뉴스 격리와 같은 성격).

덤프는 reports/_debug/에 쌓인다. GitHub Actions 러너는 일회용이라 로컬 파일이 잡 종료와
함께 사라지는데, 워크플로우가 이미 `git add -f reports/`로 재귀 커밋하고 있어 별도 설정
없이 레포에 영구 보존된다. .gitignore의 `reports/` 때문에 로컬 실행분은 실수로 커밋되지
않는다(워크플로우만 -f로 강제).
"""
import json
import logging
import math
import os
import re
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

logger = logging.getLogger(__name__)

_KST = ZoneInfo("Asia/Seoul")
_ET = ZoneInfo("America/New_York")  # 시장 시간 가설 재검증용 — 사고 시각을 ET로도 남긴다

_PROJECT_ROOT = Path(__file__).parent.parent.parent
# 모듈 레벨 상수 — 테스트가 monkeypatch로 갈아끼운다
# (html_report_generator._REPORTS_DIR와 같은 패턴)
_DEBUG_DIR = _PROJECT_ROOT / "reports" / "_debug"

# 심볼에 ^GSPC의 '^', USDKRW=X의 '=' 같은 문자가 있어 파일명으로 바로 못 쓴다
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")

_GITHUB_ENV_KEYS = (
    "GITHUB_RUN_ID",
    "GITHUB_RUN_NUMBER",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_EVENT_NAME",
    "GITHUB_WORKFLOW",
)


def dump_nan_incident(
    *,
    source: str,
    symbol: str,
    period: str,
    history: pd.DataFrame,
    extra: dict | None = None,
) -> str | None:
    """NaN이 섞인 history를 증거 파일로 남기고 경로를 반환한다. 실패 시 None.

    Args:
        source: 어느 fetcher인지 ("stock" | "index" | "exchange").
        symbol: 조회 심볼. 파일명에 새니타이즈해서 들어간다.
        period: yfinance에 실제로 요청한 period 문자열.
        history: yfinance가 돌려준 원본 DataFrame(가공 전).
        extra: 야후 응답 메타(history_metadata). 없으면 None.

    반환 경로는 로깅용이다. 호출측은 이 값을 신뢰해 분기하면 안 된다 —
    덤프 실패는 조용히 None이 된다.
    """
    try:
        now_utc = datetime.now(timezone.utc)
        payload = {
            "detected_at": {
                "utc": now_utc.isoformat(),
                "kst": now_utc.astimezone(_KST).isoformat(),
                "et": now_utc.astimezone(_ET).isoformat(),
            },
            "source": source,
            "symbol": symbol,
            "period_requested": period,
            "versions": _versions(),
            "github": _github_env(),
            "nan_summary": _nan_summary(history),
            "history": _history_records(history),
            "history_metadata": extra,
        }

        _DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        filename = (
            f"nan_{now_utc.strftime('%Y%m%dT%H%M%SZ')}"
            f"_{source}_{_sanitize(symbol)}.json"
        )
        path = _DEBUG_DIR / filename
        # allow_nan=False — NaN/Infinity 리터럴은 표준 JSON이 아니라 jq 등이 못 읽는다.
        # 값 변환(_jsonable)에서 이미 None으로 바꿨으므로 여기선 검증 역할.
        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
                default=str,
            ),
            encoding="utf-8",
        )
        return str(path)
    except Exception as e:
        # 진단 실패가 리포트 생성을 막으면 안 된다.
        logger.warning(f"NaN 덤프 실패 ({source}/{symbol}): {e}")
        return None


def _sanitize(symbol: str) -> str:
    """심볼 → 파일명에 안전한 문자열. '^GSPC' → '_GSPC', 'USDKRW=X' → 'USDKRW_X'."""
    return _UNSAFE_FILENAME_CHARS.sub("_", str(symbol)) or "unknown"


def _versions() -> dict:
    """설치된 패키지 버전. 핀 갱신 후 재발 여부를 추적하는 데 쓴다.

    importlib.metadata를 쓰는 이유: yfinance를 import하지 않고 버전만 읽기 위해서.
    common/은 벤더 라이브러리에 의존하지 않는다.
    """
    versions: dict[str, str | None] = {}
    for package in ("yfinance", "pandas"):
        try:
            versions[package] = metadata.version(package)
        except Exception:
            versions[package] = None
    return versions


def _github_env() -> dict:
    """Actions 실행 컨텍스트. 로컬 실행이면 전부 빈 문자열."""
    return {
        key.removeprefix("GITHUB_").lower(): os.getenv(key, "")
        for key in _GITHUB_ENV_KEYS
    }


def _nan_summary(history: pd.DataFrame) -> dict:
    """어느 컬럼·어느 날짜가 깨졌는지 한눈에 보이는 요약."""
    is_na = history.isna()
    return {
        "row_count": int(len(history)),
        "columns_with_nan": [
            str(column) for column in history.columns if bool(is_na[column].any())
        ],
        "nan_row_dates": [
            _index_label(index)
            for index, flagged in is_na.any(axis=1).items()
            if bool(flagged)
        ],
    }


def _history_records(history: pd.DataFrame) -> list[dict]:
    """DataFrame 전체를 JSON 레코드로. 전 컬럼·전 행 보존.

    이 덤프의 핵심이다. Close만 null인지, OHLC 중 뭐가 살아있는지, Volume은 얼마인지가
    여기서 갈린다 (yfinance는 OHLCV가 전부 NaN/0일 때만 행을 버리므로, 살아남은 행에는
    반드시 뭔가 값이 남아있다).
    """
    # object 캐스팅 후 NaN → None. float NaN인 채로 두면 JSON 직렬화가 막힌다.
    safe = history.astype(object).where(pd.notna(history), None)
    records = []
    for index, row in safe.iterrows():
        record: dict = {"date": _index_label(index)}
        for column, value in row.items():
            record[str(column)] = _jsonable(value)
        records.append(record)
    return records


def _index_label(index) -> str:
    """DatetimeIndex 항목 → ISO 문자열. 타임존이 붙어있으면 그대로 보존한다
    (야후가 어느 거래소 시간대로 응답했는지도 증거다)."""
    isoformat = getattr(index, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    return str(index)


def _jsonable(value):
    """numpy 스칼라·NaN·Inf를 JSON이 받을 수 있는 값으로."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        # np.float64는 float 서브클래스라 여기서 함께 걸린다.
        return value if math.isfinite(value) else None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return value
    # np.int64 등 — 파이썬 스칼라로 내린다 (플랫폼에 따라 int 서브클래스가 아니다).
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return _jsonable(item())
        except Exception:
            pass
    return str(value)
