"""定期訪問を集めるの壊しかた。読むだけ・写しをそのまま。"""

from __future__ import annotations

from app.dto.pattern_row import PatternRow
from app.services.screen.gather_patterns import gather_patterns


class 取り決めの偽物:
    def read_all(self) -> tuple[PatternRow, ...]:
        return (PatternRow(id="1", patient="P-001", weekday="Mon", every_weeks="1", clinician="Dr-A",
                           purpose="weekly", active_from="2026-08-01", active_to=None),)

    def add(
        self, patient: str, weekday: str, clinician: str, purpose: str, start: str,
        every_weeks: str = "1", *, by: str = "",
    ) -> str | None:
        return None

    def end(self, pattern_id: str, on: str, by: str) -> str | None:
        return None


def test_写しをそのまま運ぶ() -> None:
    rows = gather_patterns(取り決めの偽物())
    assert rows[0].patient == "P-001"
