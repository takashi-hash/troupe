"""答える — 答え待ち → 着手できる。

設計: 設計/仕事とは何か.md §6 遷移表・不変条件 I7・設計/仕事が回る筋道.md §1。
| 答え待ち | **着手できる** | 答える `answer` | `QuestionAnswered` | **人** |

**人しか起こせない**（I7 公理の執行者）——`Answer` の `by` が `Human` なので、
AI が答える行は型検査が赤にする。
**戻り先は着手できる**——実行中へ戻すと、答えを待っているあいだに
担当が外れた仕事を誰も拾えない（AI は着手できるを取りに来る）。
だから**誰の担当が外れたか**が出来事に残る。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import AwaitingAnswer, Ready
from domain.events.job.question_answered import QuestionAnswered
from domain.values.job.answer import Answer


def answer(
    job: Job[AwaitingAnswer], ans: Answer, now: datetime
) -> tuple[Job[Ready], QuestionAnswered]:
    """答えを渡して着手できるへ戻す。返るのは（着手できる仕事, 答えられた）の対。"""
    unassigned = job.state.assignee
    data = fields_of(job) | {"state": Ready()}
    return Job[Ready].model_validate(data), QuestionAnswered(
        at=now, by=ans.by, body=ans.body, unassigned=unassigned
    )
