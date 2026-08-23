"""点数表の行の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.fee_row import FeeRow


def make_row(**over: object) -> FeeRow:
    data: dict[str, object] = {
        "code": "NV01", "name": "Home visit (single home)", "kind": "visit",
        "points": 800, "price_yen": None, "unit": "per_day",
        "weekly_cap": 3, "note": "",
    }
    return FeeRow.model_validate(data | over)


def test_欄は設計の点数表の行そのまま() -> None:
    assert set(FeeRow.model_fields) == {
        "code", "name", "kind", "points", "price_yen", "unit", "weekly_cap", "note",
    }


def test_薬剤は円で持てる() -> None:
    row = make_row(kind="drug", points=None, price_yen="21.50", unit="per_event", weekly_cap=None)
    assert row.points is None and row.price_yen == "21.50"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_row().points = 999  # type: ignore[misc]
