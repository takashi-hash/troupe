"""時刻の口の壊しかた。domain は「いま」を取りに行かない——取りに行くのはここだけ。"""

from __future__ import annotations

from datetime import datetime
from typing import get_type_hints

from app.ports.clock_port import ClockPort


def test_出すのはいまの時刻だけ() -> None:
    assert get_type_hints(ClockPort.now)["return"] is datetime
