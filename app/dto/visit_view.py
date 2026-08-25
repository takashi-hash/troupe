"""訪問の詳細 — 当日入力の画面が見る、文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2。
| 訪問の詳細 | 訪問の識別子・日付・患者の要約（患者の行の全欄）・**その訪問宛ての
未消費の下書き（高々1つ）**・**署名済みの記録の列**・**行為の列**・担当の名簿 |

**下書きが初期値、人が書き上げ、署名で事実になる。** ここは材料を運ぶだけ。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientNote


class UnusedDraft(BaseModel):
    """その訪問宛ての未消費の下書き — 署名の初期値になる提案。

    (患者, 訪問日) に一度しか置けないので高々1つ。消費されたかは
    記録の存在から導く——下書き自身は印を持たない。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    body: str
    delivered_at: str


class VisitView(BaseModel):
    """訪問の詳細 — 当日入力の材料ぜんぶ。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    visit_date: str
    clinician: str
    purpose: str
    status: str
    patient: PatientRow
    #: その訪問（患者・訪問日）宛ての未消費の下書き。無ければ空——白紙から書いて署名してよい。
    draft: UnusedDraft | None
    #: 署名済みの記録（新しい順）。実施済みの訪問を開いたときは自分の記録が先頭に居る。
    notes: tuple[PatientNote, ...]
    #: 署名者の名簿。初期値は担当。
    clinicians: tuple[str, ...]
    #: 行為の列 — (コード, 名称, 数量)。署名前は編集でき、署名で凍る。
    services: tuple[tuple[str, str, int], ...] = ()
