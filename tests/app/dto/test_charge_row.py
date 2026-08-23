"""算定の行の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.charge_row import ChargeRow


def make_row(**over: object) -> ChargeRow:
    data: dict[str, object] = {
        "id": "17", "patient": "P-001", "day": "2026-08-20", "code": "NV01",
        "name": "Home visit (single home)", "qty": 1, "points": 800,
        "status": "derived", "flag_reason": None, "resolve_reason": None,
        "visit_id": "31",
    }
    return ChargeRow.model_validate(data | over)


def test_欄は設計の算定の行そのまま() -> None:
    assert set(ChargeRow.model_fields) == {
        "id", "patient", "day", "code", "name", "qty", "points",
        "status", "flag_reason", "resolve_reason", "visit_id",
    }


def test_旗の行は理由と0点を運べる() -> None:
    row = make_row(status="flagged", points=0, flag_reason="Weekly cap (3) exceeded")
    assert row.points == 0 and row.flag_reason


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_row().points = 0  # type: ignore[misc]
