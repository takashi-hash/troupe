"""対象期間 — その仕事が担当する期間。

設計: 設計/仕事とは何か.md §2「決まり」・§3・§7「禁止値」。
| `Period` | 月なら `2026-08`、週なら `2026-W34` の形だけ | `Period("来月")` が通ったら赤 |

**形から周期が読める。** だから `cycle` を返せる——別に持たせると2つがずれる。
**周期といまからも出せる**（`Period.of`）——`reconcile` が対象期間も決める
（設計/仕事が回る筋道.md §2）。いまは引数で受け取る（domain に時計は置けない）。
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Final, Self

from pydantic import model_validator

from domain.values.calendar.cycle import Cycle
from domain.obligations import Value

#: 月の形 — `2026-08`。**月は 01〜12 だけ。**
_MONTHLY_FORM: Final = re.compile(r"\d{4}-(0[1-9]|1[0-2])")

#: 週の形 — `2026-W34`。**週は W01〜W53 だけ。**
_WEEKLY_FORM: Final = re.compile(r"\d{4}-W(0[1-9]|[1-4]\d|5[0-3])")


class Period(Value):
    """対象期間 — 月なら `2026-08`、週なら `2026-W34`。**その2つの形だけ。**"""

    text: str

    @property
    def cycle(self) -> Cycle:
        """形から読める周期。"""
        if _WEEKLY_FORM.fullmatch(self.text):
            return Cycle.WEEKLY
        return Cycle.MONTHLY

    @classmethod
    def of(cls, now: datetime, cycle: Cycle) -> Self:
        """いまと周期から出す。週なら ISO 週 `2026-W34`、月なら `2026-08` の形。"""
        if cycle is Cycle.WEEKLY:
            iso = now.isocalendar()
            return cls(text=f"{iso.year}-W{iso.week:02d}")
        return cls(text=f"{now.year}-{now.month:02d}")

    @model_validator(mode="after")
    def _obligations(self) -> Self:
        if not (_MONTHLY_FORM.fullmatch(self.text) or _WEEKLY_FORM.fullmatch(self.text)):
            raise ValueError(
                f"対象期間の形が違います: {self.text!r}。月は 2026-08、週は 2026-W34 の形だけ"
            )
        return self
