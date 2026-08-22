"""確かめ期日が先へ送られた — 引用が取れず、次に確かめる時刻が先へ進んだ、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 確かめ期日が先へ送られた | 新しい確かめ期日 | `RecheckDatePushed` |

**時計が主語。** 足して残るのは新しい確かめ期日だけ——誰が・いつは共通が持つ。
"""

from __future__ import annotations

from datetime import datetime

from domain.events.event import Event


class RecheckDatePushed(Event):
    """確かめ期日が先へ送られた。"""

    #: 新しい確かめ期日 — 送られた先の時刻。
    recheck_at: datetime
