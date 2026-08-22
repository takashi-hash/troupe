"""成果 — 仕事が生んだもの。

設計: 設計/仕事とは何か.md §2「仕事」・§3。
| `Result` | **中身が空でない**。出したあと差し替えられない。**在りかは持たない**——積んだ Store が返し、仕事が持つ | 中身空で作れたら赤／在りかの欄があったら赤 |

**在りかは持たない。** 積んだ Store が在りかを返し、仕事がそれを持つ。
成果自身が自分の置き場を知ると、積む前と積んだあとで別のものになる。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class Result(Value):
    """成果 — 出したら書き換えない。中身だけを持つ。"""

    body: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "成果の中身")
        return self
