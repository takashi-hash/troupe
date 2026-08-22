"""詳細の壊しかた。設計/人に見えるもの.md §2。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.detail_view import DetailView
from app.dto.event_row import EventRow


def make_view(**over: object) -> DetailView:
    data: dict[str, object] = {
        "id": "J-0001",
        "state_name": "AwaitingApproval",
        "due": "2026-08-20T09:00:00+00:00",
        "assignee_name": "座長",
        "result_body": "2026-W34 の依存の一覧",
        "evidence_quote": None,
        "recheck_at": None,
        "question_body": None,
        "answer_body": None,
        "assessments": (),
        "actions": ("approve", "send_back"),
        "events": (EventRow(at="2026-08-18T09:02:00+00:00", by="AI", what="成果が出された"),),
    }
    return DetailView.model_validate(data | over)


def test_欄は設計の詳細そのまま() -> None:
    """仕事の識別子・状態の名・期日・担当・成果の中身・根拠の引用・確かめ期日・
    質問の本文・回答の本文・見立ての本文と理由・押せること・出来事の列。"""
    assert set(DetailView.model_fields) == {
        "id",
        "state_name",
        "due",
        "assignee_name",
        "result_body",
        "evidence_quote",
        "recheck_at",
        "question_body",
        "answer_body",
        "assessments",
        "actions",
        "events",
    }


def test_文字とIDだけ_domainの値は運ばない() -> None:
    """出来事の列も出来事の行（文字）で持つ。"""
    for name, field in DetailView.model_fields.items():
        assert "domain" not in str(field.annotation), f"{name} が domain の値を運んでいる"


def test_出来事の列を持つ() -> None:
    assert make_view().events[0].what == "成果が出された"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        make_view().state_name = "Cleared"  # type: ignore[misc]
