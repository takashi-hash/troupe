"""答えられた — 人が質問に答えた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| **答えられた** | 誰が・何と ＋ **誰の担当が外れたか** | `QuestionAnswered` |

**人が主語**（I7）。誰がは共通の `by` が持つ。
答えたら「着手できる」へ戻る——だから**誰の担当が外れたか**が残る。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.events.event import Event
from domain.values.people.human import Human
from domain.obligations import not_blank
from domain.values.people.assignee import Assignee


class QuestionAnswered(Event):
    """答えられた。「判断は人間」の実物のひとつ。"""

    #: **人が主語**——太字が型になる。AI や時計がこの手を起こした形は書けない。
    by: Human  # pyright: ignore[reportIncompatibleVariableOverride]

    #: 中身 — 何と答えたか。空でない。
    body: str

    #: 誰の担当が外れたか。
    unassigned: Assignee

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "答えの中身")
        return self
