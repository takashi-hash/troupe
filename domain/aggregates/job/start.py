"""着手する — 着手できる → 実行中。

設計: 設計/仕事とは何か.md §6 遷移表・不変条件 I13・設計/仕事が回る筋道.md §1「AI が始めるもの」。
| 着手できる | 実行中 | 着手する `start` | `JobStarted` | **取ろうとする AI**（まだ担当ではない） |

**取るだけは別**（I13）——取る前は担当ではないから、`by` は取ろうとする AI。
`by` の型が `Agent` なので、人や時計が取る行は型検査が赤にする。
取れるかは型が決める——判断ではない。取った AI がここから担当になる。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import InProgress, Ready
from domain.events.job.job_started import JobStarted
from domain.value_objects.people.agent import Agent


def start(
    job: Job[Ready], by: Agent, now: datetime
) -> tuple[Job[InProgress], JobStarted]:
    """仕事を取る。返るのは（実行中の仕事, 着手された）の対——I1 が型になる。"""
    data = fields_of(job) | {"state": InProgress(assignee=by)}
    return Job[InProgress].model_validate(data), JobStarted(at=now, by=by, took=by)
