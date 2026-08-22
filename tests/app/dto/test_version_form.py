"""版の欄の壊しかた。文字と数だけ——domain の値は入らない。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.version_form import VersionForm


def test_書かなかった欄は_None_のまま() -> None:
    form = VersionForm(instruction="依存の一覧を取る")
    assert form.instruction == "依存の一覧を取る" and form.source is None


def test_知らない欄では作れない() -> None:
    with pytest.raises(ValidationError):
        VersionForm(急ぎ=True)  # type: ignore[call-arg]


def test_文字と数だけで組める() -> None:
    """ui が domain を知らずに組めることの証明。"""
    VersionForm(
        instruction="依存の一覧を取り更新が来ているものを挙げる",
        source="file:custom/deps.txt",
        required_terms=("{対象期間}",),
        description="一覧の日付が今週のものである",
        cycle="weekly",
        days=3,
        budget_calls=20,
        budget_seconds=600,
        owner="座長",
        max_retries=20,
    )
