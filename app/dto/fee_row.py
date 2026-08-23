"""点数表の行 — 会計と当日入力の画面が見る、マスタの写し。

設計: 設計/人に見えるもの.md §2。
| 点数表の行 | コード・名称・種別（訪問/臨時/行為/薬剤/材料/加算/月次）・点数または円・
算定単位・上限・注記 |

**全部架空**——実在の点数表の構造だけを写した Nagisa Schedule。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FeeRow(BaseModel):
    """点数表の行 — 1項目1行。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    name: str
    #: 種別 — visit / oncall / act / drug / material / addon / monthly。
    kind: str
    #: 点数（行為・加算・訪問・月次）。薬剤・材料は円で持つので None。
    points: int | None
    #: 円（薬剤・材料）。点数はここから換算——薬剤は五捨五超入、材料は四捨五入。
    price_yen: str | None
    #: 算定単位 — per_visit / per_event / per_day / per_week / per_month / per_quarter。
    unit: str
    #: 週の上限（訪問料の週3回など）。無ければ None。
    weekly_cap: int | None
    note: str
