"""患者の行の壊しかた。人に見えるもの §2——文字と ID だけ・振る舞いを持たない。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.patient_row import PatientRow


def _行(**over: object) -> PatientRow:
    data: dict[str, object] = {
        "code": "P-001",
        "age": "82",
        "living": "lives alone",
        "diagnosis": "CHF, NYHA II",
        "next_visit": "2026-08-24 (Dr-A)",
        "order_expires": "2026-08-13",
    }
    return PatientRow.model_validate(data | over)


def test_文字とIDだけで組める() -> None:
    行 = _行()
    assert 行.code == "P-001"
    assert 行.order_expires == "2026-08-13"


def test_予定も指示書も無い患者は空で持てる() -> None:
    """欄が無いことと、欄が空なことは別——写しは穴をそのまま写す。"""
    行 = _行(next_visit=None, order_expires=None)
    assert 行.next_visit is None and 行.order_expires is None


def test_知らない欄は入らない() -> None:
    with pytest.raises(ValidationError):
        _行(name="実名は欄そのものが無い")


def test_書き換えられない() -> None:
    with pytest.raises(ValidationError):
        _行().code = "P-999"  # type: ignore[misc]
