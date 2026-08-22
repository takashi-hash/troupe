"""着手された — 着手できる仕事を AI が取った、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 着手された | 誰が取ったか | `JobStarted` |

取るのは**取ろうとする AI**（まだ担当ではない）——取ったかどの型が `Agent` なので、
人が取った形は書けない。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.value_objects.people.agent import Agent


class JobStarted(Event):
    """着手された。取った AI がここから担当になる。"""

    #: 誰が取ったか — 取ろうとする AI。
    took: Agent
