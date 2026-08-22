"""履歴の読みの壊しかた。設計/仕事が回る筋道.md §4・人に見えるもの.md §2——文字と ID だけ。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from app.ports.history_reader import HistoryEntry, HistoryReader


def _材料() -> HistoryEntry:
    return HistoryEntry(
        at="2026-08-22 09:00",
        by_kind="clock",
        by_name=None,
        name="JobCreated",
        job_id="J-0001",
        rule="週次の依存の棚卸し",
        period="2026-W34",
        instruction="依存の一覧を突き合わせる",
    )


def test_読みは新しい順に上限つき() -> None:
    hints = get_type_hints(HistoryReader.read_latest)
    assert hints["limit"] is int
    assert hints["return"] == tuple[HistoryEntry, ...]
    assert list(inspect.signature(HistoryReader.read_latest).parameters) == ["self", "limit"]


def test_欄は出来事と見出しの材料だけ() -> None:
    """時刻・誰が・何が・仕事の識別子・業務ルール・対象期間・やること。"""
    assert set(HistoryEntry.model_fields) == {
        "at", "by_kind", "by_name", "name", "job_id", "rule", "period", "instruction",
    }


def test_文字とIDだけで_domainの値は出ない() -> None:
    for name, field in HistoryEntry.model_fields.items():
        assert "domain" not in str(field.annotation), f"{name} が domain の値を運んでいる"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        _材料().name = "JobStarted"  # type: ignore[misc]
