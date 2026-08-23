"""患者の行 — 患者の画面が見る、文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2。
| 患者の行 | 患者記号・年齢・生活状況・主病名・次の訪問・指示書の期限（**よその語のまま**） |

**診療録はよそのコンテキスト。** ここに入るのは写しであって、一座の語ではない
——だから翻訳しない。**画面に届くのは文字と ID だけ。振る舞いを持たない。**
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PatientRow(BaseModel):
    """患者の行 — 1患者1行。診療録の写し。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    age: str
    living: str
    diagnosis: str
    #: 次の訪問（日付と担当）。予定が無ければ None。
    next_visit: str | None
    #: 指示書の期限。指示書が無ければ None。
    order_expires: str | None
