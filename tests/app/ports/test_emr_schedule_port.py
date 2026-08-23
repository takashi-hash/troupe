"""予定づくりの口の宣言の壊しかた。筋道 §4——取り決め由来の予定だけ。"""

from __future__ import annotations

from app.ports.emr_schedule_port import EmrSchedulePort


class 予定づくりの偽物:
    def plan(self, days_ahead: int) -> tuple[str, ...]:
        return ("P-001 2026-08-24",)


def test_宣言は名乗りだけで満たせる() -> None:
    口: EmrSchedulePort = 予定づくりの偽物()
    assert 口.plan(28) == ("P-001 2026-08-24",)
