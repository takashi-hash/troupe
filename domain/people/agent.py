"""AI — 仕事をこなす働き手。

設計: 設計/仕事とは何か.md §2「人と場」・§3。
| `Agent` | 名が空でない | 空で作れたら赤 |

**働き手としての AI は中・中核。** LLM を呼ぶ道具は外・汎用で、別のもの。
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class Agent(Value):
    """AI — 担当を持ち、取り・尋ね・出し・落ち・見立てを書く。**判断はしない。**"""

    kind: Literal["agent"] = "agent"
    name: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.name, "AI の名")
        return self
