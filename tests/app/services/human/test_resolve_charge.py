"""旗の行を裁くの壊しかた。allow は理由必須——摘要の写し。"""

from __future__ import annotations

from app.services.human.resolve_charge import resolve_charge


class 請求の口の偽物:
    def __init__(self, answer: str | None = None) -> None:
        self._answer = answer

    def resolve(self, charge_id: str, action: str, reason: str, by: str) -> str | None:
        self.got = (charge_id, action, reason, by)
        return self._answer

    def confirm(self, patient: str, month: str, by: str) -> str | None:
        return None


def test_理由つきの特例は通る() -> None:
    口 = 請求の口の偽物()
    assert resolve_charge(口, "17", "allow", "acute exacerbation on 08-19", by="Director") is None
    assert 口.got == ("17", "allow", "acute exacerbation on 08-19", "Director")


def test_理由の無い特例は断り() -> None:
    断り = resolve_charge(請求の口の偽物(), "17", "allow", "  ", by="Director")
    assert 断り is not None and "reason" in 断り.reason


def test_落とすのに理由は要らない() -> None:
    assert resolve_charge(請求の口の偽物(), "17", "drop", "", by="Director") is None


def test_知らない裁きは断り() -> None:
    assert resolve_charge(請求の口の偽物(), "17", "maybe", "x", by="Director") is not None
