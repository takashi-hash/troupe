"""請求の写し — 会計の画面が見る、1患者1月の請求。

設計: 設計/人に見えるもの.md §2。
| 請求の写し | 患者・月・状態（下書き/確定）・総点数・負担割合・負担額・算定行の列・
誰がいつ確定したか |
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.dto.charge_row import ChargeRow


class ClaimView(BaseModel):
    """請求の写し — 確定の写しから提出ファイルと患者請求書が出る。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient: str
    month: str
    #: 状態 — draft / confirmed。
    status: str
    total_points: int
    copay_rate: int
    copay_yen: int
    confirmed_by: str | None
    confirmed_at: str | None
    charges: tuple[ChargeRow, ...]
