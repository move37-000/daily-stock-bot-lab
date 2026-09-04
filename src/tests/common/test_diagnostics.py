"""dump_nan_incident 단위 테스트.

검증 책임:
1. 덤프 파일 생성 + 스키마 (NaN이 JSON null로, 원본 행/컬럼 전부 보존)
2. nan_summary 정확성 (어느 컬럼·어느 날짜가 깨졌는지)
3. 파일명 새니타이즈 (^GSPC, USDKRW=X)
4. **어떤 입력에도 예외를 던지지 않는다** — 진단 도구가 본체를 죽이면 안 된다

야후의 결손 자체는 재현할 수 없지만, 결손을 만났을 때 이 코드가 뭘 하는지는
전부 재현 가능하다. NaN DataFrame을 직접 만들어 넣는다.
"""
import json

import pandas as pd
import pytest

from src.common import diagnostics
from src.common.diagnostics import dump_nan_incident


@pytest.fixture(autouse=True)
def _debug_dir(tmp_path, monkeypatch):
    """덤프 위치를 tmp_path로 격리. 실제 reports/_debug/를 건드리지 않는다."""
    target = tmp_path / "_debug"
    monkeypatch.setattr(diagnostics, "_DEBUG_DIR", target)
    return target


def _nan_history() -> pd.DataFrame:
    """마지막 행 Close만 null인 실제 사고 형태.

    yfinance는 OHLCV가 전부 NaN/0일 때만 행을 버리므로, 실제 사고에서도
    Open/High/Low/Volume은 살아있었을 가능성이 높다. 그 형태를 재현한다.
    """
    return pd.DataFrame(
        {
            "Open": [930.0, 955.0],
            "High": [935.0, 960.0],
            "Low": [928.0, 950.0],
            "Close": [932.86, float("nan")],
            "Volume": [1_000_000, 2_000_000],
        },
        index=pd.to_datetime(["2026-09-02", "2026-09-03"]),
    )


def _dump(**overrides) -> dict:
    """덤프를 실행하고 기록된 JSON을 파싱해 돌려준다."""
    kwargs = {
        "source": "stock",
        "symbol": "MU",
        "period": "5d",
        "history": _nan_history(),
    }
    kwargs.update(overrides)
    path = dump_nan_incident(**kwargs)
    assert path is not None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestDumpContent:
    def test_파일_생성_및_경로_반환(self, _debug_dir):
        path = dump_nan_incident(
            source="stock", symbol="MU", period="5d", history=_nan_history()
        )

        assert path is not None
        assert list(_debug_dir.glob("*.json")) != []

    def test_NaN이_JSON_null로_직렬화(self):
        payload = _dump()

        rows = payload["history"]
        assert len(rows) == 2
        assert rows[1]["Close"] is None
        # 나머지 컬럼은 살아있어야 한다 — 이게 사고 분석의 핵심 정보다.
        assert rows[1]["Open"] == 955.0
        assert rows[1]["Volume"] == 2_000_000
        assert rows[0]["Close"] == 932.86

    def test_전체_컬럼_보존(self):
        payload = _dump()

        assert set(payload["history"][0]) == {
            "date", "Open", "High", "Low", "Close", "Volume",
        }

    def test_nan_summary(self):
        summary = _dump()["nan_summary"]

        assert summary["row_count"] == 2
        assert summary["columns_with_nan"] == ["Close"]
        assert len(summary["nan_row_dates"]) == 1
        assert summary["nan_row_dates"][0].startswith("2026-09-03")

    def test_시각을_UTC_KST_ET_세_가지로_기록(self):
        """다음 사고 때 시장 시간 가설을 즉시 재검증하려면 ET가 필요하다."""
        detected_at = _dump()["detected_at"]

        assert set(detected_at) == {"utc", "kst", "et"}

    def test_컨텍스트_필드(self):
        payload = _dump(source="index", symbol="^GSPC", period="7d")

        assert payload["source"] == "index"
        assert payload["symbol"] == "^GSPC"
        assert payload["period_requested"] == "7d"
        assert "yfinance" in payload["versions"]
        assert "run_id" in payload["github"]

    def test_history_metadata_전달(self):
        payload = _dump(extra={"exchangeTimezoneName": "America/New_York"})

        assert payload["history_metadata"] == {
            "exchangeTimezoneName": "America/New_York"
        }

    def test_metadata_없으면_null(self):
        assert _dump()["history_metadata"] is None

    def test_엄격한_JSON_NaN_리터럴_없음(self, _debug_dir):
        """jq 등 표준 파서로 읽을 수 있어야 한다. NaN/Infinity 리터럴은 표준 JSON이 아니다."""
        dump_nan_incident(
            source="stock", symbol="MU", period="5d", history=_nan_history()
        )
        raw = next(_debug_dir.glob("*.json")).read_text(encoding="utf-8")

        assert "NaN" not in raw
        # parse_constant는 NaN/Infinity 리터럴을 만날 때만 호출된다.
        json.loads(raw, parse_constant=lambda c: pytest.fail(f"비표준 리터럴: {c}"))


class TestFilenameSanitize:
    @pytest.mark.parametrize(
        "symbol, expected_fragment",
        [
            ("MU", "_stock_MU.json"),
            ("^GSPC", "_index__GSPC.json"),
            ("USDKRW=X", "_exchange_USDKRW_X.json"),
        ],
    )
    def test_심볼_특수문자_치환(self, symbol, expected_fragment, _debug_dir):
        source = {"MU": "stock", "^GSPC": "index", "USDKRW=X": "exchange"}[symbol]

        path = dump_nan_incident(
            source=source, symbol=symbol, period="5d", history=_nan_history()
        )

        assert path.endswith(expected_fragment)


class TestNeverRaises:
    """진단 도구는 어떤 상황에서도 파이프라인을 죽이면 안 된다.

    실패하면 조용히 None을 반환하고 경고만 남긴다.
    """

    def test_history가_None이어도_raise_안_함(self):
        assert dump_nan_incident(
            source="stock", symbol="MU", period="5d", history=None
        ) is None

    def test_Close_컬럼이_없어도_raise_안_함(self):
        history = pd.DataFrame({"Foo": [1, 2]}, index=pd.to_datetime(
            ["2026-09-02", "2026-09-03"]
        ))

        assert dump_nan_incident(
            source="stock", symbol="MU", period="5d", history=history
        ) is not None

    def test_직렬화_불가_metadata여도_raise_안_함(self):
        """history_metadata에 datetime 등이 섞여 들어와도 덤프는 남아야 한다."""
        payload = _dump(extra={"weird": object()})

        assert payload["history_metadata"]["weird"].startswith("<object object")

    def test_디렉터리_생성_실패해도_raise_안_함(self, monkeypatch, tmp_path):
        # _DEBUG_DIR 자리에 파일을 놔서 mkdir을 실패시킨다.
        blocker = tmp_path / "blocked"
        blocker.write_text("not a directory", encoding="utf-8")
        monkeypatch.setattr(diagnostics, "_DEBUG_DIR", blocker)

        assert dump_nan_incident(
            source="stock", symbol="MU", period="5d", history=_nan_history()
        ) is None
