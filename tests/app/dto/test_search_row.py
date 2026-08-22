"""検索の行の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.search_row import SearchRow


def make_row(**over: object) -> SearchRow:
    data: dict[str, object] = {
        "id": "J-0001",
        "head": "週次の依存の棚卸し　2026-W34",
        "period": "2026-W34",
        "instruction": "依存の一覧を突き合わせる",
        "state_name": "終わった",
        "due": "2026-08-20 09:00",
        "assignee_name": None,
    }
    return SearchRow.model_validate(data | over)


def test_欄は設計の検索の行そのまま() -> None:
    """仕事の識別子・見出し・対象期間・やること・状態の名・期日・担当の名。"""
    assert set(SearchRow.model_fields) == {
        "id", "head", "period", "instruction", "state_name", "due", "assignee_name",
    }


def test_文字とIDだけ_domainの値は運ばない() -> None:
    for name, field in SearchRow.model_fields.items():
        assert "domain" not in str(field.annotation), f"{name} が domain の値を運んでいる"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_row().state_name = "着手できる"  # type: ignore[misc]
