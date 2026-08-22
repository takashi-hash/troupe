"""今日の材料 — 仕様が見る、仕事1件ぶんの domain の値。

設計: 設計/人に見えるもの.md §2・仕事が回る筋道.md §4（`TodayReader`）。
「**今日の材料**（仕様が見る domain の値）と**今日の行**（画面が見る文字）は別物——
`gather_today` が 材料 → 仕様 → 行 の順に詰め替える」。
欄は「今日の行から押せることを除いたもの」を **domain の値**で持つ。
押せることを持たないのは、押せることが**この材料から仕様が組むもの**だから。
"""

from __future__ import annotations

from datetime import datetime

from domain.obligations import Value
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.due_date import DueDate
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.spent import Spent
from domain.value_objects.people.owner import Owner
from domain.value_objects.rule.budget import Budget
from domain.value_objects.rule.instruction import Instruction
from domain.value_objects.rule.rule_name import RuleName


class TodayMaterial(Value):
    """今日の材料 — 仕様（今日に出すか・押せること）が見る材料。1仕事1件。"""

    #: 仕事の識別子。
    id: JobId

    #: `RuleName` と生まれた版の番号 — 業務ルール発のみ。依頼発は空。
    rule: RuleName | None
    born_version: int | None

    #: 対象期間 — 業務ルール発のみ。
    period: Period | None

    #: 依頼の中身の先頭 — 依頼発のみ。
    request_head: str | None

    #: やること — 生まれたとき写したもの（依頼発は依頼の中身）。
    instruction: Instruction

    #: 状態の名。
    state_name: str

    #: 期日。
    due: DueDate

    #: 担当の名 — 居なければ空。
    assignee_name: str | None

    #: 確かめ期日 — 自己申告（根拠なしで終わった）だけが持つ。
    recheck_at: datetime | None

    #: 成果の中身・根拠の引用・質問の本文・回答の本文 — 出てから持つ。
    result_body: str | None
    evidence_quote: str | None
    question_body: str | None
    answer_body: str | None

    #: 見立て — 本文とそう読んだ理由。そのまま届く。
    assessments: tuple[Assessment, ...]

    #: やり直した回数と上限 — 尽きたかは下の導出が言う（式の正本はここ1つ）。
    retried: int
    max_retries: int

    #: 使った量と上限。
    spent: Spent
    budget: Budget

    #: 受け持ちの人。
    owner: Owner

    @property
    def retries_exhausted(self) -> bool:
        """やり直しが尽きたか——今日の行の欄はここから導く。"""
        return self.retried >= self.max_retries
