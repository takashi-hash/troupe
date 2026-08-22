"""周期 — 月か週。

設計: 設計/仕事とは何か.md §2「決まり」・§3。
| `Cycle` | 月か週のどちらか | 3つ目の値が通ったら赤 |

**幅を持つのは確かめ期日のため。**
| `RecheckDate` | **前の確かめ期日（無ければ期日）＋写した周期**——AI が決めるのではない |
"""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum


class Cycle(StrEnum):
    """周期 — 月か週。**3つ目は無い。** 業務ルールの版が持ち、仕事へ写す。"""

    MONTHLY = "monthly"
    WEEKLY = "weekly"

    @property
    def span(self) -> timedelta:
        """先へ送る幅。月は31日、週は7日。**確かめ期日がこれを足す。**"""
        if self is Cycle.MONTHLY:
            return timedelta(days=31)
        return timedelta(days=7)
