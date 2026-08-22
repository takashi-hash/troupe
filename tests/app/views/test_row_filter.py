"""絞り込みの条件の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.views.row_filter import RowFilter


def test_欄はキーワードと状態の表示と業務ルールと担当() -> None:
    assert set(RowFilter.model_fields) == {"keyword", "state_label", "rule", "assignee"}


def test_文字だけ() -> None:
    for name, field in RowFilter.model_fields.items():
        assert field.annotation == (str | None), f"{name} が文字ではない"


def test_空の欄は絞らないを意味するので空で作れる() -> None:
    assert RowFilter() == RowFilter(keyword=None, state_label=None, rule=None, assignee=None)


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        RowFilter().keyword = "依存"  # type: ignore[misc]
