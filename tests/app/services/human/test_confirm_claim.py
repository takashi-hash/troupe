"""月次請求を確定するの壊しかた。"""

from __future__ import annotations

from app.services.human.confirm_claim import confirm_claim


class 請求の口の偽物:
    def __init__(self, answer: str | None = None) -> None:
        self._answer = answer

    def resolve(self, charge_id: str, action: str, reason: str, by: str) -> str | None:
        return None

    def confirm(self, patient: str, month: str, by: str) -> str | None:
        self.got = (patient, month, by)
        return self._answer


def test_通れば確定が渡る() -> None:
    口 = 請求の口の偽物()
    assert confirm_claim(口, "P-001", "2026-07", by="Director") is None
    assert 口.got == ("P-001", "2026-07", "Director")


def test_名の無い確定は断り() -> None:
    assert confirm_claim(請求の口の偽物(), "P-001", "2026-07", by=" ") is not None


def test_口の断りは理由になって返る() -> None:
    断り = confirm_claim(請求の口の偽物("The month is not over yet"), "P-001", "2026-08", by="Director")
    assert 断り is not None and "not over" in 断り.reason
