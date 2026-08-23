"""患者の詳細の壊しかた。人に見えるもの §2——押せることは無い・読むだけの写し。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.patient_view import PatientDraft, PatientNote, PatientView


def _詳細(**over: object) -> PatientView:
    data: dict[str, object] = {
        "code": "P-003",
        "age": "76",
        "living": "lives with spouse",
        "diagnosis": "Parkinson's disease",
        "next_visit": "2026-08-25 (Dr-A)",
        "order": "certification, expires 2026-12-19",
        "meds": ("levodopa/carbidopa 100/25 tid",),
        "events": ("2026-08-02: fall at home",),
        "drafts": (
            PatientDraft(delivered_at="2026-08-24 09:00", body="SOAP draft", job_id="J-1"),
        ),
        "notes": (
            PatientNote(
                at="2026-08-11", clinician="Dr-A", s="s", o="o", a="a", p="p",
                signed_at="2026-08-11 16:05",
            ),
        ),
    }
    return PatientView.model_validate(data | over)


def test_カルテ抽出が丸ごと入る() -> None:
    詳細 = _詳細()
    assert 詳細.notes[0].clinician == "Dr-A"
    assert 詳細.events[0].startswith("2026-08-02")


def test_下書きと署名済みは別の欄() -> None:
    """提案と事実を1つの列に混ぜない——下書きには署名の欄が無く、記録には仕事の欄が無い。"""
    詳細 = _詳細()
    assert 詳細.drafts[0].job_id == "J-1"
    assert not hasattr(詳細.drafts[0], "signed_at")
    assert not hasattr(詳細.notes[0], "job_id")
    assert 詳細.notes[0].signed_at


def test_押せることの欄がそもそも無い() -> None:
    """読むだけの写し——actions を持たせようとしても入らない。"""
    with pytest.raises(ValidationError):
        _詳細(actions=("approve",))


def test_書き換えられない() -> None:
    with pytest.raises(ValidationError):
        _詳細().code = "P-999"  # type: ignore[misc]
