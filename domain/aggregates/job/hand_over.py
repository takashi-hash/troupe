"""人へ回す — 見立てを書いて、人の判断を待つ。

設計: 設計/仕事とは何か.md §6 遷移表・仕事が回る筋道.md §1「AI が始めるもの」。
| 実行中 | 失敗した | **人へ回す** `hand_over` | `AssessmentWritten`＋`JobFailed` | AI（**もう自力では進めないと見た**） |
| 失敗した | 失敗した | **人へ回す** `hand_over` | `AssessmentWritten` | AI（上限に達した・やり直しが尽きた） |

**進めないという事実の報告**——どうするかは人が決める。
実行中からは、落ちた中身に**見立ての本文（finding）をそのまま置く**。
失敗したからは、状態は失敗したのまま、見立てだけ刻む。
から状態で残る出来事が違うので `@typing.overload`——突合が型注釈を読む。
"""

from __future__ import annotations

from datetime import datetime
from typing import overload

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import Failed, InProgress
from domain.events.job.assessment_written import AssessmentWritten
from domain.events.job.job_failed import JobFailed
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.people.agent import Agent


@overload
def hand_over(
    job: Job[InProgress], assessment: Assessment, by: Agent, now: datetime
) -> tuple[Job[Failed], AssessmentWritten, JobFailed]: ...


@overload
def hand_over(
    job: Job[Failed], assessment: Assessment, by: Agent, now: datetime
) -> tuple[Job[Failed], AssessmentWritten]: ...


def hand_over(
    job: Job[InProgress] | Job[Failed],
    assessment: Assessment,
    by: Agent,
    now: datetime,
) -> tuple[Job[Failed], AssessmentWritten, JobFailed] | tuple[Job[Failed], AssessmentWritten]:
    """見立てを刻む。実行中からは、落ちたことも必ず一緒に刻む——I1 が型になる。"""
    written = AssessmentWritten(at=now, by=by, assessment=assessment)
    if isinstance(job.state, InProgress):
        data = fields_of(job) | {"state": Failed(fallen=assessment.finding)}
        return (
            Job[Failed].model_validate(data),
            written,
            JobFailed(at=now, by=by, fallen=assessment.finding),
        )
    return Job[Failed].model_validate(fields_of(job)), written
