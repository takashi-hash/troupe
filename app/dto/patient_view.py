"""患者の詳細 — 1人のカルテ抽出を画面が見る形で。文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2。
| 患者の詳細 | 患者の行の全欄＋処方の列・状態変化の列・診療記録の列（日付・担当・S・O・A・P）。
**押せることは無い**——読むだけの写し |

診療記録（`PatientNote`）がここに同居するのは、詳細の外で診療記録を運ぶ者が居ないから。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PatientNote(BaseModel):
    """診療記録1件 — S・O・A・P。よその書式のまま。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    at: str
    nurse: str
    s: str
    o: str
    a: str
    p: str


class PatientView(BaseModel):
    """患者の詳細 — 押せることは無い。読むだけの写し。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    age: str
    living: str
    diagnosis: str
    next_visit: str | None
    order: str | None
    meds: tuple[str, ...]
    events: tuple[str, ...]
    notes: tuple[PatientNote, ...]
