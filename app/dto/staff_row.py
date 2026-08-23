"""席と役の行 — 切り替えの選びと押せることの出し分けが見る写し。

設計: 設計/人に見えるもの.md §2。
| 席と役の行 | 席の名・役（director／clinician） |
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StaffRow(BaseModel):
    """席と役の行 — 1職員1行。役の正本はデータ（診療録の staff）。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    #: 役 — director / clinician。
    role: str
