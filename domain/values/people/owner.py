"""受け持ちの人 — 承認をし、AI の質問を受ける人。版が決める。

設計: 設計/仕事とは何か.md §2「仕事」・§3・不変条件 I6。
| `Owner` | **`Human` そのもの**。AI は受け持ちの人になれない | `Agent` から作れたら赤 |

**公理「判断は人間」が、ここで型になる。**
担当は人か AI だが、受け持ちの人は人だけ。
"""

from __future__ import annotations

from domain.obligations import Value
from domain.values.people.human import Human


class Owner(Value):
    """受け持ちの人 — 承認できるのはこの人だけ（I6）。AI の質問もこの人へ行く。"""

    person: Human
