"""もう一度やった — 何度目のやり直しかが残った、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| もう一度やった | 何度目か | `Retried` |

足して残るのは何度目かだけ。**1以上**——0度目のやり直しは無い。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.events.event import Event


class Retried(Event):
    """もう一度やった。"""

    #: 何度目か — 1以上。
    times: int

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.times < 1:
            raise ValueError("何度目かは1以上です")
        return self
