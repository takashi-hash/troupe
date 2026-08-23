"""予定を組むの壊しかた。筋道 §1——取り決めの展開は帳簿づけ・運ぶだけ。"""

from __future__ import annotations

from app.services.clock.plan_visits import HORIZON_DAYS, plan_visits


class 予定づくりの偽物:
    def __init__(self) -> None:
        self.頼まれた: list[int] = []

    def plan(self, days_ahead: int) -> tuple[str, ...]:
        self.頼まれた.append(days_ahead)
        return ("P-001 2026-08-24", "P-003 2026-08-25")


def test_先の分を頼んで見出しを返す() -> None:
    口 = 予定づくりの偽物()
    assert plan_visits(口) == ("P-001 2026-08-24", "P-003 2026-08-25")
    assert 口.頼まれた == [HORIZON_DAYS]
