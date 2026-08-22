"""今日の行の壊しかた。設計/人に見えるもの.md §2（正本）。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.today_row import TodayRow


def make_row(**over: object) -> TodayRow:
    data: dict[str, object] = {
        "id": "J-0001",
        "rule": "週次の依存の棚卸し",
        "born_version": 1,
        "period": "2026-W34",
        "request_head": None,
        "instruction": "依存の一覧を突き合わせる",
        "state_name": "AwaitingApproval",
        "due": "2026-08-20T09:00:00+00:00",
        "assignee_name": "座長",
        "recheck_at": None,
        "result_body": "2026-W34 の依存の一覧",
        "evidence_quote": None,
        "question_body": None,
        "answer_body": None,
        "assessments": (),
        "retries_exhausted": False,
        "spent_calls": 3,
        "spent_seconds": 60,
        "budget_calls": 20,
        "budget_seconds": 600,
        "owner_name": "座長",
        "actions": ("approve", "send_back"),
    }
    return TodayRow.model_validate(data | over)


def test_文字とIDだけ_domainの値は運ばない() -> None:
    """集約も値オブジェクトも出さない。"""
    for name, field in TodayRow.model_fields.items():
        assert "domain" not in str(field.annotation), f"{name} が domain の値を運んでいる"


def test_見立ては本文と理由がそのまま届く() -> None:
    """縮めない——縮めると人が判断する材料が減る。"""
    row = make_row(
        assessments=(("20回とも同じ理由で落ちた", "源の在りかが変わった可能性が高い"),)
    )
    assert row.assessments[0] == ("20回とも同じ理由で落ちた", "源の在りかが変わった可能性が高い")


def test_押せることの欄を持つ() -> None:
    assert make_row().actions == ("approve", "send_back")


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_row().state_name = "Ready"  # type: ignore[misc]
