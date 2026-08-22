"""回答 — 人が答えた事実。

設計: 設計/仕事とは何か.md §2「仕事」・§3・不変条件 I7。
| `Answer` | 答えた人と中身を持つ | どちらか欠けて作れたら赤 |

**答えを起こせるのは人だけ**（I7）——AI を受ける欄は無い。

**答えは根拠にならない。** 人が答えた中身は、材料であって裏づけではない。
終わったと言える裏づけは源から読んだ引用（`Evidence`）だけなので、
ここに根拠の欄は無い。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank
from domain.value_objects.people.human import Human


class Answer(Value):
    """回答 — 答えた人と中身。答えたら仕事は着手できるへ戻る。"""

    #: 答えた人。**AI は答えない**（I7）。
    by: Human
    #: 答えの中身。人が書く。
    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "回答の中身")
        return self
