"""承認された — 人が「進んでよい」と決めた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| **承認された** | — | `Approved` |

**人が主語。** 足して残るものは無い——誰が・いつは共通が持つ。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.values.people.human import Human


class Approved(Event):
    """承認された。「判断は人間」の実物のひとつ。"""

    #: **人が主語**——太字が型になる。AI や時計がこの手を起こした形は書けない。
    by: Human  # pyright: ignore[reportIncompatibleVariableOverride]
