"""時間切れで戻った — 期限の切れた担当が外れた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 時間切れで戻った | 誰の担当だったか | `JobTimedOut` |

**時計が起こす。** 切れていないものは触らない——何度回しても同じ結果になる。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.values.people.assignee import Assignee


class JobTimedOut(Event):
    """時間切れで戻った。仕事は着手できるへ戻る。"""

    #: 誰の担当だったか — 外れた担当。人か AI。
    was: Assignee
