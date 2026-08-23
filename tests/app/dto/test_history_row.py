"""履歴の行の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.history_row import HistoryRow


def make_row(**over: object) -> HistoryRow:
    data: dict[str, object] = {
        "at": "2026-08-22 09:00",
        "by": "時計",
        "by_kind": "clock",
        "what": "仕事が作られた",
        "job_id": "J-0001",
        "head": "週次の依存の棚卸し　2026-W34",
    }
    return HistoryRow.model_validate(data | over)


def test_欄は設計の履歴の行そのまま() -> None:
    """時刻・誰が（種別と名）・何が起きたか・仕事の識別子・見出し。"""
    assert set(HistoryRow.model_fields) == {"at", "by", "by_kind", "what", "job_id", "head"}


def test_文字とIDだけ_domainの値は運ばない() -> None:
    for name, field in HistoryRow.model_fields.items():
        assert "domain" not in str(field.annotation), f"{name} が domain の値を運んでいる"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_row().what = "着手された"  # type: ignore[misc]
