"""予定づくりへの口。**取り決め由来の予定だけを作る。**

設計: 設計/仕事が回る筋道.md §4。
| `EmrSchedulePort` | Port | 有効な取り決めと既にある予定の鍵を読み、**取り決め由来の
予定だけ**を診療録に作る——臨時・中止・署名済みに書く口は無い | **app** | adapters | `plan_visits` |

冪等は診療録の一意の鍵（取り決め×日付）が決める——**何度回しても同じ**。
"""

from __future__ import annotations

from typing import Protocol


class EmrSchedulePort(Protocol):
    def plan(self, days_ahead: int) -> tuple[str, ...]:
        """先の分の予定をまだ無ければ作り、新しく作った分の見出しを返す。

        届かなければ空——次の脈がまた来る。
        """
        ...
