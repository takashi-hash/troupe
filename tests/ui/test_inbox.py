"""受信箱の参照名の壊しかた——どの患者かは源の在りかが知っている（配達と同じ読みかた）。"""

from __future__ import annotations

from app.dto.today_row import TodayRow
from ui.web.inbox import _参照名  # pyright: ignore[reportPrivateUsage]


def _row(**over: object) -> TodayRow:
    data: dict[str, object] = {
        "id": "J-0001",
        "rule": "Visit Note Draft",
        "born_version": 1,
        "period": "2026-W35",
        "request_head": None,
        "instruction": "Read the patient chart in the source.",
        "source": "db:chart/P-004",
        "state_name": "承認待ち",
        "due": "2026-08-26 00:00",
        "assignee_name": "座長",
        "recheck_at": None,
        "result_body": None,
        "evidence_quote": None,
        "question_body": None,
        "answer_body": None,
        "assessments": (),
        "retries_exhausted": False,
        "spent_calls": 1,
        "spent_seconds": 60,
        "budget_calls": 12,
        "budget_seconds": 300,
        "owner_name": "座長",
        "actions": ("approve",),
    }
    return TodayRow.model_validate(data | over)


def test_カルテの仕事は源から患者を読む() -> None:
    """ルール名から切り出さない——汎用ルール1本でも患者チップが立つ。"""
    badge, 参照, code = _参照名(_row())
    assert badge == "Visit note"
    assert 参照 == "P-004 · Visit note · 2026-W35"
    assert code == "P-004"


def test_カルテ以外の源のルールはレポートのまま() -> None:
    badge, 参照, code = _参照名(_row(rule="Billing Integrity Check", source="db:billing"))
    assert badge == "Report"
    assert code is None
