"""起こす者 — その手を起こした者。

設計: 設計/仕事とは何か.md §2「仕事」・設計/仕事が回る筋道.md §5。
| `Actor` | **人・AI・時計の3つのどれか**。素の文字列から作れない | 4つ目が作れたら赤 |

**すべての出来事が「いつ・誰が」を持つ。** その「誰が」がこれ。
**担当とは別。** 画面は起こさない——開いた人が起こす者。
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from domain.values.people.agent import Agent
from domain.values.people.clock import Clock
from domain.values.people.human import Human

#: 起こす者 — 人・AI・時計のどれか。**4つ目は無い。**
Actor = Annotated[Human | Agent | Clock, Field(discriminator="kind")]
