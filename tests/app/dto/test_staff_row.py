"""席と役の行の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.staff_row import StaffRow


def test_欄は設計の席と役の行そのまま() -> None:
    assert set(StaffRow.model_fields) == {"name", "role"}


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        StaffRow(name="Director", role="director").role = "clinician"  # type: ignore[misc]
