"""道順の行 — 道順の画面が見る、1訪問1行の入れ物。

設計: 設計/人に見えるもの.md §2。
| 道順の行 | 順番・患者記号・場所の名（公共の代役）・予定の目的・拠点からの距離 |

座標を持つのは**地図を描くため**——実在の自宅は1つも指さない（場所は公共の代役）。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RouteStop(BaseModel):
    """道順の行 — 並び順つきの1訪問。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    seq: int
    visit_id: str
    prep: str
    status: str
    patient: str
    place: str
    purpose: str
    #: 前の地点からの距離（km、表示用の文字）。
    leg_km: str
    lat: float
    lng: float
