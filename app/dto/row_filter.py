"""絞り込みの条件 — 検索の画面から受け取る、文字だけの入れ物。

設計: 設計/人に見えるもの.md §2。
| 絞り込みの条件 | キーワード・状態の表示・業務ルール・担当（**文字だけ**） |

**文字だけ。振る舞いを持たない。** ただの入れ物。空の欄は絞らない。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RowFilter(BaseModel):
    """絞り込みの条件 — 欄はどれも文字。空なら絞らない。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    keyword: str | None = None
    state_label: str | None = None
    rule: str | None = None
    assignee: str | None = None
