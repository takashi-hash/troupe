"""訪問の詳細の壊しかた。人に見えるもの §2——下書きが初期値・押せるのは2つだけ。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientNote
from app.dto.visit_view import UnusedDraft, VisitView


def _訪問(**over: object) -> VisitView:
    data: dict[str, object] = {
        "id": "7", "visit_date": "2026-08-25", "clinician": "Dr-A",
        "purpose": "weekly visit", "status": "scheduled",
        "patient": PatientRow(code="P-003", age="76", living="x", diagnosis="PD",
                              next_visit=None, order_expires=None),
        "drafts": (UnusedDraft(id="3", body="draft body", delivered_at="2026-08-24 09:00"),),
        "notes": (PatientNote(at="2026-08-11", clinician="Dr-A", s="s", o="o", a="a",
                              p="p", signed_at="2026-08-11 16:05"),),
        "clinicians": ("Dr-A", "Dr-B", "Dr-C"),
    }
    return VisitView.model_validate(data | over)


def test_当日入力の材料が丸ごと入る() -> None:
    v = _訪問()
    assert v.drafts[0].id == "3" and v.clinicians[0] == "Dr-A"


def test_押せることの欄はそもそも無い() -> None:
    with pytest.raises(ValidationError):
        _訪問(actions=("approve",))


def test_書き換えられない() -> None:
    with pytest.raises(ValidationError):
        _訪問().status = "done"  # type: ignore[misc]
