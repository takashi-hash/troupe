"""出す — 実行中 → 提出済み。

設計: 設計/仕事とは何か.md §6 遷移表・設計/仕事が回る筋道.md §1「AI が始めるもの」。
| 実行中 | 提出済み | 出す `submit` | `ResultSubmitted` | 担当 |

**合否は決めない。** 成果の在りかを仕事に持たせる。
**源をもう一度読んで引用が取れれば**根拠も積む。取れなければ根拠なしで出す
——だから根拠の在りかだけが空でありうる。
提出済みは成果の在りかが空でない——仕事の義務が守る。
**起こす者は担当そのもの**——`by` に担当を入れる。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import InProgress, Submitted
from domain.events.job.result_submitted import ResultSubmitted


def submit(
    job: Job[InProgress], result_at: str, evidence_at: str | None, now: datetime
) -> tuple[Job[Submitted], ResultSubmitted]:
    """成果を出す。返るのは（提出済みの仕事, 成果が出された）の対——I1 が型になる。"""
    data = fields_of(job) | {
        "state": Submitted(assignee=job.state.assignee),
        "result_at": result_at,
        "evidence_at": evidence_at,
    }
    return Job[Submitted].model_validate(data), ResultSubmitted(
        at=now, by=job.state.assignee, result_at=result_at, evidence_at=evidence_at
    )
