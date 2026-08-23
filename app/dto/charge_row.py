"""算定の行 — 会計の画面が見る、導出された1行。

設計: 設計/人に見えるもの.md §2。
| 算定の行 | 識別子・患者・日付・コード・名称・数量・点数・状態（導出/旗/裁かれて通った/
落とした）・旗の理由・裁きの理由 |
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChargeRow(BaseModel):
    """算定の行 — 1算定1行。旗の行は点数0で人の裁きを待つ。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    patient: str
    day: str
    code: str
    name: str
    qty: int
    points: int
    #: 状態 — derived / flagged / allowed / dropped。
    status: str
    flag_reason: str | None
    resolve_reason: str | None
    visit_id: str | None
