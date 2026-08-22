"""人 — 判断する者。

設計: 設計/仕事とは何か.md §2「人と場」・§3。
| `Human` | 名が空でない | 空で作れたら赤 |
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class Human(Value):
    """人 — 判断する者。承認・差し戻し・回答・有効化・打ち切りは人しか起こせない。"""

    kind: Literal["human"] = "human"
    name: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.name, "人の名")
        return self
