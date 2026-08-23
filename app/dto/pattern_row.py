"""取り決めの行 — 定期訪問の画面が見る、文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2。
| 取り決めの行 | 識別子・患者記号・曜日・担当・目的・始まり・終わり |

**取り決めは診療録（よそのコンテキスト）のマスタ。** 写しであって、一座の語ではない。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PatternRow(BaseModel):
    """取り決めの行 — 1取り決め1行。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    patient: str
    #: 曜日の名（Mon..Sun）。数字の橋は adapters が持つ。
    weekday: str
    #: 週の間隔（1=毎週、2=隔週…）。文字で運ぶ。
    every_weeks: str
    clinician: str
    purpose: str
    active_from: str
    #: 終わりの日。無ければ続いている。
    active_to: str | None
