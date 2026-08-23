"""取り決めの行の壊しかた。人に見えるもの §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.pattern_row import PatternRow


def _行(**over: object) -> PatternRow:
    data: dict[str, object] = {
        "id": "1", "patient": "P-001", "weekday": "Mon", "clinician": "Dr-A",
        "purpose": "weekly visit", "active_from": "2026-08-01", "active_to": None,
    }
    return PatternRow.model_validate(data | over)


def test_続いている取り決めは終わりが無い() -> None:
    assert _行().active_to is None


def test_知らない欄は入らない() -> None:
    with pytest.raises(ValidationError):
        _行(住所="欄そのものが無い")


def test_書き換えられない() -> None:
    with pytest.raises(ValidationError):
        _行().patient = "P-999"  # type: ignore[misc]
