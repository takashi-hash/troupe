"""今日の材料の壊しかた。設計/人に見えるもの.md §2・仕事が回る筋道.md §4（`TodayReader`）。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.value_objects.job.today_material import TodayMaterial
from tests.services.conftest import make_material


def test_欄は今日の行から押せることを除いたもの() -> None:
    """正本（人に見えるもの §2）との突合。押せることは仕様が組むので、欄が無い。"""
    assert set(TodayMaterial.model_fields) == {
        "id",
        "rule",
        "born_version",
        "period",
        "request_head",
        "instruction",
        "state_name",
        "due",
        "assignee_name",
        "recheck_at",
        "result_body",
        "evidence_quote",
        "question_body",
        "answer_body",
        "assessments",
        "retries_exhausted",
        "spent",
        "budget",
        "owner",
    }


def test_同じ中身なら等しい() -> None:
    assert make_material() == make_material()


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_material().state_name = "Ready"  # type: ignore[misc]


def test_知らない欄では作れない() -> None:
    with pytest.raises(ValidationError):
        make_material(actions=("approve",))
