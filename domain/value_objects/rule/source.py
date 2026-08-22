"""源 — 材料の在りか。**AI が読みに行く先。**

設計: 設計/仕事とは何か.md §2「決まり」・§3。
| `Source` | 在りかが空でない | 空で作れたら赤 |

**在りかだけを持つ。** 読んだ中身は持たない——読むのは外で、
外の言葉は腐敗防止層を通ってから中へ入る。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class Source(Value):
    """源 — AI がどこを読むか。版が持ち、仕事へ写される。"""

    location: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.location, "源の在りか")
        return self
