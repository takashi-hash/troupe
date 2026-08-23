"""患者の詳細 — 1人のカルテ抽出を画面が見る形で。文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2。
| 患者の詳細 | 患者の行の全欄＋処方の列・状態変化の列・診療記録の列（日付・担当・S・O・A・P）。
**押せることは無い**——読むだけの写し |

診療記録（`PatientNote`）がここに同居するのは、詳細の外で診療記録を運ぶ者が居ないから。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PatientNote(BaseModel):
    """署名済みの記録1件 — S・O・A・P。よその書式のまま。**final は不変。**"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    at: str
    clinician: str
    s: str
    o: str
    a: str
    p: str
    signed_at: str


class PatientDraft(BaseModel):
    """下書き1件 — Troupe が下書き受けに置いた提案。**署名前。記録ではない。**"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    delivered_at: str
    body: str
    #: どの仕事から来たか——帳簿の側の一生（承認の出来事）に辿れる。
    job_id: str


class PatientView(BaseModel):
    """患者の詳細 — 押せることは無い。読むだけの写し。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    age: str
    living: str
    diagnosis: str
    next_visit: str | None
    order: str | None
    #: いま継続中の処方だけ。
    meds: tuple[str, ...]
    events: tuple[str, ...]
    #: 下書き（提案）と署名済み（事実）は**別の欄**——1つの列に混ぜない。
    drafts: tuple[PatientDraft, ...]
    notes: tuple[PatientNote, ...]
