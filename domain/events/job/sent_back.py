"""差し戻された — 人が「まだだ」と決めた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| **差し戻された** | 誰が・理由 | `SentBack` |

**人が主語。** 誰がは共通の `by` が持つ——足して残るのは理由だけ。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.events.event import Event
from domain.values.people.human import Human
from domain.obligations import not_blank


class SentBack(Event):
    """差し戻された。「判断は人間」の実物のひとつ。"""

    #: **人が主語**——太字が型になる。AI や時計がこの手を起こした形は書けない。
    by: Human  # pyright: ignore[reportIncompatibleVariableOverride]

    #: 理由 — 空でない。
    reason: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.reason, "差し戻しの理由")
        return self
