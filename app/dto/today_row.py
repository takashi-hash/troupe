"""今日の行 — 押しつけの画面が見る、文字と ID の入れ物。

設計: 設計/人に見えるもの.md §2（**正本**）。
| 今日の行（**正本**） | 仕事の識別子・`RuleName` と生まれた版の番号・**対象期間**（依頼発は依頼の中身の先頭）・**やること**（生まれたとき写したもの——**元の内容が無いと承認しようがない**）・**源の在りか**（カルテの仕事はここから患者が読める）・状態の名・期日・担当の名・確かめ期日・**成果の中身**・**根拠の引用**・**質問の本文**・**回答の本文**・**見立ての本文と理由**・**やり直しが尽きたか**・**使った量と上限**・受け持ちの人・**押せること** |

**画面に届くのは文字と ID だけ。** 集約も値オブジェクトも出さない。
**振る舞いを持たない。** ただの入れ物。
本文をそのまま載せる。**押しつけの画面でだけ縮めない**——縮めると押す前に読めない。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TodayRow(BaseModel):
    """今日の行 — 1仕事1行。`gather_today` が 材料 → 仕様 → 行 の順に詰め替える。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    rule: str | None
    born_version: int | None
    period: str | None
    request_head: str | None
    #: やること — 生まれたとき写したもの。元の内容が無いと承認しようがない。
    instruction: str
    #: 源の在りか — カルテの仕事はここから患者が読める。
    source: str
    state_name: str
    due: str
    assignee_name: str | None
    recheck_at: str | None
    result_body: str | None
    evidence_quote: str | None
    question_body: str | None
    answer_body: str | None
    #: 見立て — （本文, そう読んだ理由）の列。そのまま届く。
    assessments: tuple[tuple[str, str], ...]
    retries_exhausted: bool
    #: 使った量と上限。
    spent_calls: int
    spent_seconds: int
    budget_calls: int
    budget_seconds: int
    owner_name: str
    #: 押せること — 組むのは domain の仕様。画面は入っているものを出すだけ。
    actions: tuple[str, ...]
