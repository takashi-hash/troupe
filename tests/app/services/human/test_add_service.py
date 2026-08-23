"""行為を足すの壊しかた。数に読めない数量は断り・空の名は断り。"""

from __future__ import annotations

from app.services.human.add_service import add_service


class 行為の口の偽物:
    def __init__(self, answer: str | None = None) -> None:
        self._answer = answer

    def add(self, visit_id: str, code: str, qty: int, by: str) -> str | None:
        self.got = (visit_id, code, qty, by)
        return self._answer

    def remove(self, visit_id: str, code: str) -> str | None:
        return None


def test_通れば行為が載る() -> None:
    口 = 行為の口の偽物()
    assert add_service(口, "31", "NP03", "2", by="Dr-A") is None
    assert 口.got == ("31", "NP03", 2, "Dr-A")


def test_数量が空なら1になる() -> None:
    口 = 行為の口の偽物()
    add_service(口, "31", "NP03", "", by="Dr-A")
    assert 口.got[2] == 1


def test_数に読めない数量は断り() -> None:
    断り = add_service(行為の口の偽物(), "31", "NP03", "two", by="Dr-A")
    assert 断り is not None and "not a number" in 断り.reason


def test_0以下の数量は断り() -> None:
    assert add_service(行為の口の偽物(), "31", "NP03", "0", by="Dr-A") is not None


def test_名の無い記帳は断り() -> None:
    assert add_service(行為の口の偽物(), "31", "NP03", "1", by=" ") is not None


def test_口の断りは理由になって返る() -> None:
    断り = add_service(行為の口の偽物("The visit is already signed"), "31", "NP03", "1", by="Dr-A")
    assert 断り is not None and "signed" in 断り.reason
