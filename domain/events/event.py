"""出来事の共通 — いつ・誰が。

設計: 設計/仕事が回る筋道.md §5「ドメインイベント」。
**過去形。観察だけ。判断を含まない。積むだけ。**

すべての出来事が「いつ・誰が」を持つ。各出来事は**それに足して残るもの**だけを書く
——共通を書き分けると、どこかで落ちる。
`at` はいまを引数で受け取る（domain に時計は置けない）。
"""

from __future__ import annotations

from datetime import datetime

from domain.obligations import Value
from domain.values.people.actor import Actor


class Event(Value):
    """出来事 — いつ・誰が起こしたか。"""

    #: いつ — 起きた時刻。引数で受け取る。
    at: datetime

    #: 誰が — 起こす者（人・AI・時計）。担当とは別。
    by: Actor
