"""手放された — 担当が仕事を離した、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 手放された | 誰が離したか | `JobReleased` |

**やめる判断ではない。** 担当を外して着手できるへ戻すだけ。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.value_objects.people.assignee import Assignee


class JobReleased(Event):
    """手放された。仕事は着手できるへ戻り、誰でもまた取れる。"""

    #: 誰が離したか — 手放した担当。人か AI。
    released: Assignee
