"""出来事の行の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.event_row import EventRow


def test_欄は時刻と誰がと何が起きたか() -> None:
    assert set(EventRow.model_fields) == {"at", "by", "what"}


def test_文字とIDだけ_domainの値は運ばない() -> None:
    for name, field in EventRow.model_fields.items():
        assert "domain" not in str(field.annotation), f"{name} が domain の値を運んでいる"


def test_作ったあと書き換えられない() -> None:
    row = EventRow(at="2026-08-18T09:02:00+00:00", by="座長", what="承認された")
    with pytest.raises(ValidationError):
        row.what = "差し戻された"  # type: ignore[misc]
