"""仕事の識別子 — 一意。あとから変えない。

設計: 設計/仕事とは何か.md §2「仕事」・§3・§7「禁止値」。
| `JobId` | 空でない。前後に空白が無い。あとから変えない | `JobId("")` が通ったら赤 |

**前後の空白を許すと、目には同じ識別子が二つになる。**
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class JobId(Value):
    """仕事の識別子 — 仕事 `Job` の同一性。生まれてから終点まで変えない。"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.text, "仕事の識別子")
        if self.text != self.text.strip():
            raise ValueError("仕事の識別子の前後に空白があります")
        return self
