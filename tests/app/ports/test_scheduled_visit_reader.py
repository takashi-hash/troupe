"""予定の訪問の読みの宣言の壊しかた。筋道 §4——穴あきの源を持つ版の展開の材料。"""

from __future__ import annotations

from app.ports.scheduled_visit_reader import ScheduledVisitReader


class 予定読みの偽物:
    def read_scheduled(self) -> tuple[tuple[str, str], ...]:
        return (("P-001", "2026-08-24"),)


def test_宣言は名乗りだけで満たせる() -> None:
    読み: ScheduledVisitReader = 予定読みの偽物()
    assert 読み.read_scheduled() == (("P-001", "2026-08-24"),)
