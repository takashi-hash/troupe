"""履歴の行 — 履歴の画面が見る、文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2。
| 履歴の行 | 時刻・誰が・何が起きたか・**仕事の識別子・見出し**（業務ルールと対象期間、無ければやることの先頭） |

**画面に届くのは文字と ID だけ。振る舞いを持たない。** ただの入れ物。
見出しが無いと、どの仕事の出来事か判らない——行から詳細が開く。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HistoryRow(BaseModel):
    """履歴の行 — 1出来事1行。新しい順に並ぶ。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    at: str
    by: str
    #: 何が起きたか — 用語集の語そのまま。
    what: str
    job_id: str
    #: 見出し — 業務ルールと対象期間、無ければやることの先頭。
    head: str
