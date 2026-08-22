"""担当 — いま仕事を持っている者。

設計: 設計/仕事とは何か.md §2「仕事」・§3。
| `Assignee` | **`Human` か `Agent` のどちらか**。3つ目は無い | 素の文字列から作れたら赤 |

**起こす者とは別。** 時計は起こすが、担当にはならない。
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from domain.values.people.agent import Agent
from domain.values.people.human import Human

#: 担当 — 人か AI のどちらか。**3つ目は無い。**
Assignee = Annotated[Human | Agent, Field(discriminator="kind")]
