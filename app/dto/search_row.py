"""検索の行 — 検索の画面が見る、文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2。
| 検索の行 | 仕事の識別子・見出し・対象期間・やること・状態の名・期日・担当の名 |

**画面に届くのは文字と ID だけ。振る舞いを持たない。** ただの入れ物。
終わったものも含めて引く（F1）——行から詳細が開く。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SearchRow(BaseModel):
    """検索の行 — 1仕事1行。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    #: 見出し — 業務ルールと対象期間、無ければやることの先頭。
    head: str
    period: str | None
    instruction: str
    #: 状態の名 — 用語集の語そのまま。
    state_name: str
    due: str
    assignee_name: str | None
