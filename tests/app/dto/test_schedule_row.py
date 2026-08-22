"""予定の行の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.schedule_row import ScheduleRow


def make_row(**over: object) -> ScheduleRow:
    data: dict[str, object] = {
        "rule": "週次の依存の棚卸し",
        "instruction": "依存の一覧を取り更新が来ているものを挙げる",
        "version": 2,
        "active_version": 1,
        "next_period": "2026-W35",
        "actions": ("add_version", "activate"),
    }
    return ScheduleRow.model_validate(data | over)


def test_欄は設計の予定の行そのまま() -> None:
    """業務ルールの名・やること・版の番号・有効な版・次の対象期間・押せること。"""
    assert set(ScheduleRow.model_fields) == {
        "rule",
        "instruction",
        "version",
        "active_version",
        "next_period",
        "actions",
    }


def test_文字とIDだけ_domainの値は運ばない() -> None:
    for name, field in ScheduleRow.model_fields.items():
        assert "domain" not in str(field.annotation), f"{name} が domain の値を運んでいる"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_row().version = 3  # type: ignore[misc]
