"""検索条件 — 何で絞れるかは、モデルの欄が決める。

**検索のキーはモデルの欄と1対1**。思いつきでキーを足さない——足したくなったら、
それはモデルに欄が足りない合図。キーの一覧はこう導かれる:

| キー | モデルのどの欄か |
|---|---|
| キーワード | 業務ルールの名（作成元）・成果物の中身・エラーの理由 |
| 状態 | タスクの状態（State） |
| 業務ルール | 作成元（FromDefinition.definition_name） |
| 担当 | 承認待ちの assignee_id ／ 札の holder |
| 期限 | 芯の deadline |

規則の三分解でいう**仕様**（これは合う（合格）か）なので、判定もここに置く。
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from domain.job import Job, assignee_of, definition_of, period_of


class SearchCriteria(BaseModel):
    """検索条件 — 空の欄は「絞らない」。全部空なら、すべてのタスクが合う"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    keyword: str = ""
    state_kind: str = ""  # 状態（State の種）
    definition_name: str = ""  # 業務ルール
    assignee: str = ""  # 担当
    deadline_from: date | None = None
    deadline_to: date | None = None


def matches(job: Job, criteria: SearchCriteria, body: str = "") -> bool:
    """合う — タスクが検索条件に合うか。body は成果物の中身（キーワードが当たる先）"""
    if criteria.state_kind and job.state.kind != criteria.state_kind:
        return False
    if criteria.definition_name and definition_of(job) != criteria.definition_name:
        return False
    if criteria.assignee and assignee_of(job) != criteria.assignee:
        return False
    deadline = job.core.deadline.date()
    if criteria.deadline_from and deadline < criteria.deadline_from:
        return False
    if criteria.deadline_to and deadline > criteria.deadline_to:
        return False
    if criteria.keyword:
        haystack = " ".join(
            [
                definition_of(job),
                period_of(job),
                job.core.job_id,
                assignee_of(job),
                body,
                getattr(job.state, "reason", "") or "",
            ]
        )
        if criteria.keyword not in haystack:
            return False
    return True
