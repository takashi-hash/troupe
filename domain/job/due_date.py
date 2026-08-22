"""期日 — 終えるべき時刻。

設計: 設計/仕事とは何か.md §2「仕事」・§3・§4「仕事が持つもの」・不変条件 I12。
| `DueDate` | 時刻を持つ。**起点の時刻を受け取って比べる**（依頼発は依頼の時刻、業務ルール発は作られた時刻） | 起点より前で作れたら赤 |

**起点と期日を両方の欄に持つ。** 片方だけを持つと、比べる相手を外から
連れてこないと確かめられない——**起点より前の期日が型で書けない**ようにするため、
起点をこの値の中に置く。

**時計は持たない。** いまが何時かは domain の外の話。起点は引数で受け取る。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Self

from pydantic import model_validator

from domain.obligations import Value


class DueDate(Value):
    """期日 — 終えるべき時刻。**起点の時刻より後**（I12）。"""

    #: 起点の時刻。依頼発は依頼の時刻、業務ルール発は作られた時刻。
    start: datetime
    #: 終えるべき時刻。
    at: datetime

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.at <= self.start:
            raise ValueError("期日が起点の時刻より後ではありません")
        return self

    @classmethod
    def from_start(cls, start: datetime, days: int) -> Self:
        """**起点の時刻 ＋ 版の日数** から組む。

        日数が足りず起点より後にならなければ、作るときに止まる。
        """
        return cls(start=start, at=start + timedelta(days=days))
