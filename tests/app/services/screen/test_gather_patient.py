"""患者の詳細を集めるの壊しかた。人に見えるもの §1・§2。"""

from __future__ import annotations

from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientView
from app.services.screen.gather_patient import gather_patient


class 診療録の偽物:
    def __init__(self, view: PatientView | None) -> None:
        self._view = view

    def read_all(self) -> tuple[PatientRow, ...]:
        return ()

    def read_one(self, code: str) -> PatientView | None:
        self.asked = code
        return self._view


def test_居ない患者はNone() -> None:
    読み = 診療録の偽物(None)
    assert gather_patient(読み, "P-999") is None
    assert 読み.asked == "P-999"


def test_写しをそのまま運ぶ() -> None:
    詳細 = PatientView(
        code="P-003", age="76", living="x", diagnosis="PD",
        next_visit=None, order=None, meds=(), events=(), notes=(),
    )
    assert gather_patient(診療録の偽物(詳細), "P-003") is 詳細
