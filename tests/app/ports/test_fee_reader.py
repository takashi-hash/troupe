"""点数表の読みの宣言の壊しかた。筋道 §4。"""

from __future__ import annotations

from app.dto.fee_row import FeeRow
from app.ports.fee_reader import FeeReader


class 点数表読みの偽物:
    def read_all(self) -> tuple[FeeRow, ...]:
        return ()


def test_宣言は名乗りだけで満たせる() -> None:
    読み: FeeReader = 点数表読みの偽物()
    assert 読み.read_all() == ()
