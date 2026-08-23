"""診療録の読みの宣言の壊しかた。筋道 §4——よそのコンテキストの写し。"""

from __future__ import annotations

from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientView
from app.ports.patient_reader import PatientReader


class 診療録の偽物:
    def read_all(self) -> tuple[PatientRow, ...]:
        return ()

    def read_one(self, code: str) -> PatientView | None:
        return None


def test_宣言は名乗りだけで満たせる() -> None:
    """Protocol——実装は adapters。宣言に振る舞いは無い。"""
    読み: PatientReader = 診療録の偽物()
    assert 読み.read_all() == ()
    assert 読み.read_one("P-001") is None
