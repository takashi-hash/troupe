"""承認 — 人が「進んでよい」と決めた事実。

設計: 設計/仕事とは何か.md §2「仕事」・§3・§7・不変条件 I4・I6・I7。
| `Approval` | **誰が**と**いつ**を両方持つ | 片方空で作れたら赤 |

**承認を起こせるのは人だけ**（I7）——AI を受ける欄は無い。
**いつを必ず持つ。** 誰が決めたかだけでは、いつ進んでよくなったのかが残らない。
承認済みはこの値を必ず持つ（I4）。

**受け持ちの人だけが承認できる**（I6）を見るのは承認の操作。
ここが持つのは、起きた事実そのもの。
"""

from __future__ import annotations

from datetime import datetime

from domain.obligations import Value
from domain.values.people.human import Human


class Approval(Value):
    """承認 — 誰がといつ。両方欠けずに揃って、はじめて先へ進める。"""

    #: 承認した人。**AI は承認しない**（I7）。
    by: Human
    #: 承認した時刻。
    at: datetime
