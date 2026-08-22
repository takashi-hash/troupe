"""質問された — 材料が足りず、AI が尋ねた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 質問された | 何を | `QuestionAsked` |

**判断は求めない**——材料の不足だけ。足して残るのは何を尋ねたかだけ。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.events.event import Event
from domain.obligations import not_blank


class QuestionAsked(Event):
    """質問された。AI から人への道の1つ。"""

    #: 中身 — 何を尋ねたか。空でない。
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "質問の中身")
        return self
