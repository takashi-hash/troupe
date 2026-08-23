"""取り決めの口の宣言の壊しかた。筋道 §4——人の操作だけが呼ぶ。"""

from __future__ import annotations

from app.dto.pattern_row import PatternRow
from app.ports.emr_pattern_port import EmrPatternPort


class 取り決めの偽物:
    def read_all(self) -> tuple[PatternRow, ...]:
        return ()

    def add(
        self, patient: str, weekday: str, clinician: str, purpose: str, start: str,
        every_weeks: str = "1",
    ) -> str | None:
        return None

    def end(self, pattern_id: str, on: str) -> str | None:
        return None


def test_宣言は名乗りだけで満たせる() -> None:
    口: EmrPatternPort = 取り決めの偽物()
    assert 口.read_all() == () and 口.add("P-001", "Mon", "Dr-A", "x", "2026-08-01") is None
