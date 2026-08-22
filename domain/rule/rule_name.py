"""業務ルールの識別子 — 一意。

設計: 設計/仕事とは何か.md §2「決まり」・§3・§4。
| `RuleName` | 空でない | `RuleName("")` が通ったら赤 |

**業務ルールの同一性はこれ。** 名が同じなら同じ業務ルールで、版を積んでも変わらない。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank


class RuleName(Value):
    """業務ルールの識別子 — 一意。版の列はこの名の下に積まれる。"""

    text: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.text, "業務ルールの名")
        return self
