"""仕事が頼まれた — 人が「これをやって」と言った、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 仕事が頼まれた | 誰が・何を | `JobRequested` |

**頼めるのは人だけ**——頼んだ人の型が `Human` なので、AI が頼んだ形は書けない。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.value_objects.people.human import Human


class JobRequested(Event):
    """仕事が頼まれた。ここから依頼発の仕事が生まれる。"""

    #: **人が主語**——太字が型になる。AI や時計がこの手を起こした形は書けない。
    by: Human  # pyright: ignore[reportIncompatibleVariableOverride]

    #: 誰が — 頼んだ人。AI は頼めない。

    #: 何を — 頼んだ中身。
    body: str
