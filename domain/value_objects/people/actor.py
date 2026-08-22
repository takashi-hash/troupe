"""起こす者 — その手を起こした者。

設計: 設計/仕事とは何か.md §2「仕事」・設計/仕事が回る筋道.md §5。
| `Actor` | **人・AI・時計の3つのどれか**。素の文字列から作れない | 4つ目が作れたら赤 |

**すべての出来事が「いつ・誰が」を持つ。** その「誰が」がこれ。
**担当とは別。** 画面は起こさない——開いた人が起こす者。
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from domain.value_objects.people.agent import Agent
from domain.value_objects.people.clock import Clock
from domain.value_objects.people.human import Human

#: 起こす者 — 人・AI・時計のどれか。**4つ目は無い。**
Actor = Annotated[Human | Agent | Clock, Field(discriminator="kind")]


#: 日本語⇄識別子の橋（人に見えるもの §2「出来事の行」の誰が）。画面の詰め替えが使う。
ACTOR_WORDS: dict[str, str] = {"人": "human", "AI": "agent", "時計": "clock"}
