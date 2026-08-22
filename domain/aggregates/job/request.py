"""頼む — （無い）→ 作られた。依頼発。

設計: 設計/仕事とは何か.md §6 遷移表・§4「仕事が持つもの」・不変条件 I3・I7・I12。
| （無い） | 作られた | 頼む `request` | `JobRequested`＋`JobCreated` | 人 |

**頼めるのは人だけ**（I7）——起こす者が `req.by`（`Human`）なので、AI が頼んだ形は書けない。
依頼発は**生まれた版と対象期間が三つとも空**。作成元は依頼の識別子（I3 の鍵）。
**期日の起点は依頼の時刻**——頼まれてから数える（I12）。
1つの遷移で出来事が2つ残る道——だから返りの出来事も2つ。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import Created
from domain.events.job.job_created import JobCreated
from domain.events.job.job_requested import JobRequested
from domain.value_objects.job.due_date import DueDate
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.origin import Origin
from domain.value_objects.job.request import Request
from domain.value_objects.job.spent import Spent
from domain.value_objects.rule.copied import Copied


def request(
    id: JobId,
    request_id: str,
    req: Request,
    copied: Copied,
    now: datetime,
) -> tuple[Job[Created], JobRequested, JobCreated]:
    """依頼から仕事を生む。返るのは（作られた仕事, 出来事2つ）——I1 が型になる。"""
    job = Job[Created](
        id=id,
        origin=Origin.from_request(request_id),
        born_of=None,
        born_version=None,
        period=None,
        instruction=copied.instruction,
        criteria=copied.criteria,
        owner=copied.owner,
        budget=copied.budget,
        source=copied.source,
        cycle=copied.cycle,
        max_retries=copied.max_retries,
        due=DueDate.from_start(req.at, copied.days),
        spent=Spent(calls=0, seconds=0),
        retried=0,
        result_at=None,
        evidence_at=None,
        state=Created(),
    )
    requested = JobRequested(at=now, by=req.by, body=req.body)
    created = JobCreated(at=now, by=req.by, rule_name=None, version=None, period=None)
    return job, requested, created
