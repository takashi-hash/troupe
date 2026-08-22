"""検査で止まった — 成果が受け入れ基準を満たさなかった、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 検査で止まった | 止めた理由 | `CheckStopped` |

**検査は止める力を持つ。** 止めたなら、なぜ止めたかが必ず残る。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.events.event import Event
from domain.obligations import not_blank


class CheckStopped(Event):
    """検査で止まった。理由の無い止まりは残せない。"""

    #: 止めた理由 — 空でない。
    reason: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.reason, "止めた理由")
        return self
