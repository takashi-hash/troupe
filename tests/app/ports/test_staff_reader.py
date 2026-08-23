"""職員の登記簿の読みの宣言の壊しかた。筋道 §4。"""

from __future__ import annotations

from app.dto.staff_row import StaffRow
from app.ports.staff_reader import StaffReader


class 登記簿読みの偽物:
    def read_all(self) -> tuple[StaffRow, ...]:
        return ()


def test_宣言は名乗りだけで満たせる() -> None:
    読み: StaffReader = 登記簿読みの偽物()
    assert 読み.read_all() == ()
