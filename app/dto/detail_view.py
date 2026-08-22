"""詳細 — この仕事は誰が・いつ・何を・どうしたかの画面が見る入れ物。

設計: 設計/人に見えるもの.md §2。
| 詳細 | 仕事の識別子・**やること**・状態の名・期日・担当・**成果の中身**・根拠の引用・確かめ期日・**問答の対の全列**・**見立ての本文と理由**・押せること・出来事の列 |

**画面に届くのは文字と ID だけ。振る舞いを持たない。** ただの入れ物。
質問・回答・見立てはそのまま届く——縮めると人が判断する材料が減る。
"""

from __future__ import annotations

from app.dto.event_row import EventRow
from pydantic import BaseModel, ConfigDict


class DetailView(BaseModel):
    """詳細 — 1仕事1枚。出来事の列は出来事の行で持つ。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    #: やること — 生まれたとき写したもの。元の内容が無いと承認しようがない。
    instruction: str
    state_name: str
    due: str
    assignee_name: str | None
    result_body: str | None
    evidence_quote: str | None
    recheck_at: str | None
    #: 質問と回答の本文——**全部**（新しいものが最後。答えの無い質問は None）
    questions: tuple[tuple[str, str | None], ...]
    #: 見立て — （本文, そう読んだ理由）の列。そのまま届く。
    assessments: tuple[tuple[str, str], ...]
    actions: tuple[str, ...]
    events: tuple[EventRow, ...]
