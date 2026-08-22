"""失敗した — 何が起きて落ちたかが残った、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 失敗した | 落ちた中身 | `JobFailed` |

足して残るのは落ちた中身だけ。**何が起きたかを残すだけ**——判断を含まない。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.events.event import Event
from domain.obligations import not_blank


class JobFailed(Event):
    """失敗した。"""

    #: 落ちた中身 — 空でない。
    fallen: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.fallen, "落ちた中身")
        return self
