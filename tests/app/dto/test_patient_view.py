"""患者の詳細の壊しかた。人に見えるもの §2——押せることは無い・読むだけの写し。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.dto.patient_view import PatientNote, PatientView


def _詳細(**over: object) -> PatientView:
    data: dict[str, object] = {
        "code": "P-003",
        "age": "76",
        "living": "lives with spouse",
        "diagnosis": "Parkinson's disease",
        "next_visit": "2026-08-25 (RN-A)",
        "order": "certification, expires 2026-12-19",
        "meds": ("levodopa/carbidopa 100/25 tid",),
        "events": ("2026-08-02: fall at home",),
        "notes": (
            PatientNote(at="2026-08-11", nurse="RN-A", s="s", o="o", a="a", p="p"),
        ),
    }
    return PatientView.model_validate(data | over)


def test_カルテ抽出が丸ごと入る() -> None:
    詳細 = _詳細()
    assert 詳細.notes[0].nurse == "RN-A"
    assert 詳細.events[0].startswith("2026-08-02")


def test_押せることの欄がそもそも無い() -> None:
    """読むだけの写し——actions を持たせようとしても入らない。"""
    with pytest.raises(ValidationError):
        _詳細(actions=("approve",))


def test_書き換えられない() -> None:
    with pytest.raises(ValidationError):
        _詳細().code = "P-999"  # type: ignore[misc]
