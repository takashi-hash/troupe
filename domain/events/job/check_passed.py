"""検査に通った — 成果が受け入れ基準を満たした、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 検査に通った | **誰へ担当が移ったか** | `CheckPassed` |

**通ったら担当を受け持ちの人へ移す**——移った先の型が `Owner` なので、
AI へ移った形は書けない（I6 の入り口）。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.values.people.owner import Owner


class CheckPassed(Event):
    """検査に通った。ここから先は人の判断を待つ。"""

    #: 誰へ担当が移ったか — 受け持ちの人。
    moved_to: Owner
