"""使った量 — これまでに使った回数と秒。

設計: 設計/仕事とは何か.md §2「仕事」・§3・§4「仕事が持つもの」・不変条件 I14。
| `Spent` | 回数も秒も**0以上**。上限とは別の値 | 負の値で作れたら赤 |

**上限とは別の値。** 仕事は `Spent(calls=0, seconds=0)` で生まれ、積むたびに新しい値になる。
上限に収まっているかは `within` が言う——**超えたときに止めるのは、積む操作の役目**（I14）。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value
from domain.value_objects.rule.budget import Budget


class Spent(Value):
    """使った量 — これまでに使った回数と秒。差し戻されたら `Spent(calls=0, seconds=0)` に戻る。"""

    calls: int
    seconds: int

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.calls < 0:
            raise ValueError("使った量の回数は0以上です")
        if self.seconds < 0:
            raise ValueError("使った量の秒は0以上です")
        return self

    def plus(self, calls: int, seconds: int) -> Spent:
        """積む。**書き換えず、積んだ結果を新しい値で返す。**"""
        return Spent(calls=self.calls + calls, seconds=self.seconds + seconds)

    def within(self, budget: Budget) -> bool:
        """使用上限に収まっているか（I14）。**上限と同じまでは収まっている。**"""
        return self.calls <= budget.calls and self.seconds <= budget.seconds
