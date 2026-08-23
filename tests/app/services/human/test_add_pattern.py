"""定期訪問を決めるの壊しかた。筋道 §1——取り決めこそが判断・空の欄は断り。"""

from __future__ import annotations

from app.services.human.add_pattern import add_pattern


class 取り決めの偽物:
    def __init__(self, なぜ: str | None = None) -> None:
        self.載せた: list[tuple[str, ...]] = []
        self._なぜ = なぜ

    def read_all(self):  # type: ignore[no-untyped-def]
        return ()

    def add(
        self, patient: str, weekday: str, clinician: str, purpose: str, start: str,
        every_weeks: str = "1",
    ) -> str | None:
        if self._なぜ:
            return self._なぜ
        self.載せた.append((patient, weekday, clinician, purpose, start, every_weeks))
        return None

    def end(self, pattern_id: str, on: str) -> str | None:
        return None


def test_通れば載る() -> None:
    口 = 取り決めの偽物()
    assert add_pattern(口, "P-001", "Mon", "Dr-A", "weekly", "2026-08-25", by="Director") is None
    assert 口.載せた == [("P-001", "Mon", "Dr-A", "weekly", "2026-08-25", "1")]


def test_誰の判断か空なら断り() -> None:
    口 = 取り決めの偽物()
    断り = add_pattern(口, "P-001", "Mon", "Dr-A", "weekly", "2026-08-25", by=" ")
    assert 断り is not None and 口.載せた == []


def test_欄が空なら断り() -> None:
    断り = add_pattern(取り決めの偽物(), "P-001", " ", "Dr-A", "weekly", "2026-08-25", by="Director")
    assert 断り is not None and "曜日" in 断り.reason


def test_診療録の断りは理由ごと届く() -> None:
    断り = add_pattern(取り決めの偽物(なぜ="その患者は居ません"), "P-999", "Mon", "Dr-A", "x", "2026-08-25", by="Director")
    assert 断り is not None and 断り.reason == "その患者は居ません"
