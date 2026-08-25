"""訪問を1回だけ休むの壊しかた。筋道 §1——理由なしでは休めない。"""

from __future__ import annotations

from app.services.human.cancel_visit import cancel_visit


class 訪問の終わりの偽物:
    def __init__(self) -> None:
        self.休んだ: list[tuple[str, str]] = []

    def sign(self, visit_id: str, signer: str, s: str, o: str, a: str, p: str) -> str | None:
        return None

    def cancel(self, visit_id: str, reason: str, by: str) -> str | None:
        self.休んだ.append((visit_id, reason))
        return None


def test_理由つきで休める() -> None:
    口 = 訪問の終わりの偽物()
    assert cancel_visit(口, "7", "patient away", by="Dr-A") is None
    assert 口.休んだ == [("7", "patient away")]


def test_理由なしでは休めない() -> None:
    口 = 訪問の終わりの偽物()
    断り = cancel_visit(口, "7", " ", by="Dr-A")
    assert 断り is not None and 口.休んだ == []
