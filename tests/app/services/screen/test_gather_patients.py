"""患者を集めるの壊しかた。人に見えるもの §1——中の語に翻訳しない・帳簿に書かない。"""

from __future__ import annotations

from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientView
from app.services.screen.gather_patients import gather_patients


class 診療録の偽物:
    def __init__(self, rows: tuple[PatientRow, ...]) -> None:
        self._rows = rows

    def read_all(self) -> tuple[PatientRow, ...]:
        return self._rows

    def read_one(self, code: str) -> PatientView | None:
        return None


def test_写しをそのまま運ぶ() -> None:
    """翻訳ゼロが仕様——よその語は一座の用語集に無い。無い橋を渡らない。"""
    行 = PatientRow(
        code="P-001", age="82", living="lives alone",
        diagnosis="CHF", next_visit=None, order_expires="2026-08-13",
    )
    assert gather_patients(診療録の偽物((行,))) == (行,)


def test_診療録が空でも画面は立つ() -> None:
    assert gather_patients(診療録の偽物(())) == ()
