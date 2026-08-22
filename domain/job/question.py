"""質問 — 材料が足りないとき AI が尋ねること。

設計: 設計/仕事とは何か.md §2「仕事」・§3・公理「判断は人間」。
| `Question` | 尋ねる中身が空でない。**相手は仕事の受け持ちの人**——AI が選ばない | 中身空で作れたら赤 |

**判断は求めない。** 尋ねるのは足りない材料であって、進めてよいかではない
（進めてよいかを問うなら、それは承認の道）。

**相手を AI が選ばない。** 受け持ちの人は版が決めるので、`Owner` を持つ。
選べるようにすると、AI が答えやすい人を選んで判断を取りに行ける。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank
from domain.people.owner import Owner


class Question(Value):
    """質問 — AI から人への道の1つ。**尋ねるのは材料で、判断ではない。**"""

    #: 尋ねる中身。足りない材料を訊く。
    body: str
    #: 尋ねる相手。**仕事の受け持ちの人**——AI が選ばない。
    to: Owner

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.body, "質問の中身")
        return self
