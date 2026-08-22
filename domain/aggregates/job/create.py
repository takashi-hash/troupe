"""作る — （無い）→ 作られた。業務ルール発。

設計: 設計/仕事とは何か.md §6 遷移表・§4「仕事が持つもの」・不変条件 I3・I12。
| （無い） | 作られた | 作る `create` | `JobCreated` | 時計 |

**時計が起こす**——有効な版といまから、まだ無い仕事を作る。
作成元は `RuleName`＋版の番号＋`Period` の鍵（I3）——何度回しても同じ結果になる。
**写すものはぜんぶ束から**——受け入れ基準は写した時点で開かれている
（`Version.copy_for` が開く）。写すのであって、指すのではない。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import Created
from domain.events.job.job_created import JobCreated
from domain.values.calendar.period import Period
from domain.values.job.due_date import DueDate
from domain.values.job.job_id import JobId
from domain.values.job.origin import Origin
from domain.values.job.spent import Spent
from domain.values.people.clock import Clock
from domain.values.rule.copied import Copied
from domain.values.rule.rule_name import RuleName


def create(
    id: JobId,
    rule: RuleName,
    version: int,
    period: Period,
    copied: Copied,
    now: datetime,
) -> tuple[Job[Created], JobCreated]:
    """仕事を生む。返るのは（作られた仕事, 仕事が作られた）の対——I1 が型になる。"""
    job = Job[Created](
        id=id,
        origin=Origin.from_rule(rule, version, period),
        born_of=rule,
        born_version=version,
        period=period,
        instruction=copied.instruction,
        criteria=copied.criteria,
        owner=copied.owner,
        budget=copied.budget,
        source=copied.source,
        cycle=copied.cycle,
        max_retries=copied.max_retries,
        due=DueDate.from_start(now, copied.days),
        spent=Spent(calls=0, seconds=0),
        retried=0,
        result_at=None,
        evidence_at=None,
        state=Created(),
    )
    return job, JobCreated(
        at=now, by=Clock(), rule_name=rule, version=version, period=period
    )
