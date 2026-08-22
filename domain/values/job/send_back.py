"""差し戻し — 人が「まだだ」と決めた事実。

設計: 設計/仕事とは何か.md §2「仕事」・§3・§7・不変条件 I7。
| `SendBack` | 理由が空でない | 理由なしで作れたら赤 |

**差し戻しを起こせるのは人だけ**（I7）——誰がの型が `Human` なので、
AI の手からこの事実が組めない。
**理由が本体。** 差し戻された仕事はやり直しへ戻るので、
理由が無いと**何を直せばよいか誰にも分からない**——それは差し戻しにならない。
"""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from domain.obligations import Value, not_blank
from domain.values.people.human import Human


class SendBack(Value):
    """差し戻し — 誰が「まだだ」と、そう言う理由。理由がやり直しの道しるべになる。"""

    #: 差し戻した人。**AI は差し戻さない**（I7）。
    by: Human

    #: なぜまだなのか。人が書く。
    reason: str

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        not_blank(self.reason, "差し戻しの理由")
        return self
