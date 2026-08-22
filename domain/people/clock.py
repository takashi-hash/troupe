"""時計 — 誰も呼ばなくても回る者。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」・§5。

起こす者にはなるが、**担当にはならない**——時計は仕事を持たない。
"""

from __future__ import annotations

from typing import Literal

from domain.obligations import Value


class Clock(Value):
    """時計 — 配る・時間切れを戻す・検査を回す・確かめる を起こす者。"""

    kind: Literal["clock"] = "clock"
