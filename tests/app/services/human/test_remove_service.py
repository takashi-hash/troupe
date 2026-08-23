"""行為を外すの壊しかた。"""

from __future__ import annotations

from app.services.human.remove_service import remove_service


class 行為の口の偽物:
    def __init__(self, answer: str | None = None) -> None:
        self._answer = answer

    def add(self, visit_id: str, code: str, qty: int, by: str) -> str | None:
        return None

    def remove(self, visit_id: str, code: str, by: str) -> str | None:
        self.got = (visit_id, code)
        return self._answer


def test_通れば外れる() -> None:
    口 = 行為の口の偽物()
    assert remove_service(口, "31", "NP03", by="Dr-A") is None
    assert 口.got == ("31", "NP03")


def test_空の指しは断り() -> None:
    assert remove_service(行為の口の偽物(), "", "NP03", by="Dr-A") is not None


def test_口の断りは理由になって返る() -> None:
    断り = remove_service(行為の口の偽物("The visit is already signed"), "31", "NP03", by="Dr-A")
    assert 断り is not None and "signed" in 断り.reason
