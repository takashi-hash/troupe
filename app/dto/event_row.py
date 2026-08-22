"""出来事の行 — 履歴と詳細が見る、文字の入れ物。

設計: 設計/人に見えるもの.md §2。
| 出来事の行 | 時刻・誰が・何が起きたか |

**画面に届くのは文字と ID だけ。振る舞いを持たない。** ただの入れ物。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EventRow(BaseModel):
    """出来事の行 — 1出来事1行。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    at: str
    by: str
    what: str
