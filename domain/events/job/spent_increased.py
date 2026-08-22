"""使った量が増えた — LLM を呼んだぶんの回数と秒が積まれた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 使った量が増えた | 増えた回数と秒 | `SpentIncreased` |

足して残るのは増えた回数と秒。どちらも0以上で、**両方0は増えていない**ので作れない。
状態は変えない——遷移表の外で刻める3つの例外のひとつ。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.events.event import Event


class SpentIncreased(Event):
    """使った量が増えた。数えるだけ——判断を含まない。"""

    #: 増えた回数 — 0以上。
    calls: int

    #: 増えた秒 — 0以上。
    seconds: int

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.calls < 0:
            raise ValueError("増えた回数は0以上です")
        if self.seconds < 0:
            raise ValueError("増えた秒は0以上です")
        if self.calls == 0 and self.seconds == 0:
            raise ValueError("回数も秒も0では増えていません")
        return self
