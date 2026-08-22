"""確かめ期日 — 根拠が無いまま終えたとき、あとで確かめる時刻。

設計: 設計/仕事とは何か.md §3・§6「状態」・不変条件 I5。
| `RecheckDate` | 時刻を持つ。**期日より後**。**前の確かめ期日（無ければ期日）＋写した周期**——AI が決めるのではない。送るたびに先へ進む | 期日より前で作れたら赤／送って進まなかったら赤 |

**基準の時刻を欄に持つ。** 基準は「前の確かめ期日（無ければ期日）」——
期日そのものを丸ごと抱えると、送っても基準が最初の期日のまま動かず、
「送って進まなかったら赤」を型が守れない。**自分の義務に要るものだけを持つ。**

**AI は決めない。** 次にいつ確かめるかは、基準に**写した周期を足した**もの。
読んだ結果ではなく、決まりから出る。
"""

from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import model_validator

from domain.calendar.cycle import Cycle
from domain.job.due_date import DueDate
from domain.obligations import Value


class RecheckDate(Value):
    """確かめ期日 — あとで確かめる時刻。**基準より後。**"""

    #: 基準 — 前の確かめ期日（はじめは期日）。これより後にしか置けない。
    after: datetime
    #: あとで確かめる時刻。
    at: datetime

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if self.at <= self.after:
            raise ValueError("確かめ期日が基準より後ではありません")
        return self

    @classmethod
    def first(cls, due: DueDate, cycle: Cycle) -> Self:
        """はじめの確かめ期日 — **期日 ＋ 写した周期**。"""
        return cls(after=due.at, at=due.at + cycle.span)

    def push(self, cycle: Cycle) -> Self:
        """先へ送る — **前の確かめ期日 ＋ 写した周期**。

        引用が取れなかったときに送る。基準が前の確かめ期日に移るので、
        **送って進まない値は型が作らせない。**
        """
        return type(self)(after=self.at, at=self.at + cycle.span)
