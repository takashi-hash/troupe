"""使用上限 — 使ってよい回数と時間。

設計: 設計/仕事とは何か.md §2「仕事」・§3・不変条件 I14。
| `Budget` | 回数も秒も**1以上** | `Budget(calls=0)` が通ったら赤 |

**暴走を止める安全弁。** 0を許すと、1回も使えない上限が書けてしまう。
**版が決める**ので、ここに置く。仕事は生まれた版から写す。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value


class Budget(Value):
    """使用上限 — 使ってよい回数と秒。**使った量はこれを超えない**（I14）。"""

    calls: int
    seconds: int

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.calls < 1:
            raise ValueError("使用上限の回数は1以上です")
        if self.seconds < 1:
            raise ValueError("使用上限の秒は1以上です")
        return self
