"""定期訪問を終えるの壊しかた。筋道 §1——列は消さない・今日づけで終える。"""

from __future__ import annotations

from app.services.human.end_pattern import end_pattern
from tests.app.services.conftest import 固定時計


class 取り決めの偽物:
    def __init__(self) -> None:
        self.終えた: list[tuple[str, str]] = []

    def read_all(self):  # type: ignore[no-untyped-def]
        return ()

    def add(self, patient: str, weekday: str, clinician: str, purpose: str, start: str) -> str | None:
        return None

    def end(self, pattern_id: str, on: str) -> str | None:
        self.終えた.append((pattern_id, on))
        return None


def test_今日づけで終える() -> None:
    口 = 取り決めの偽物()
    assert end_pattern(口, 固定時計(), "3", by="Director") is None
    assert 口.終えた == [("3", "2026-08-18")]


def test_どの取り決めか空なら断り() -> None:
    口 = 取り決めの偽物()
    assert end_pattern(口, 固定時計(), " ", by="Director") is not None
    assert 口.終えた == []
