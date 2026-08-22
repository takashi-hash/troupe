"""落ちる — 実行中 → 失敗した。

設計: 設計/仕事とは何か.md §6 遷移表・仕事が回る筋道.md §1「AI が始めるもの」。
| 実行中 | 失敗した | 落ちる `fail` | `JobFailed` | AI |

**何が起きたかを残すだけ**——判断を含まない。
`by` は担当——落ちたと言えるのは、いま持っている者だけ。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import Failed, InProgress
from domain.events.job.job_failed import JobFailed


def fail(
    job: Job[InProgress], fallen: str, now: datetime
) -> tuple[Job[Failed], JobFailed]:
    """落ちた中身を残す。返るのは（失敗した仕事, 失敗した）の対——I1 が型になる。"""
    data = fields_of(job) | {"state": Failed(fallen=fallen)}
    return Job[Failed].model_validate(data), JobFailed(
        at=now, by=job.state.assignee, fallen=fallen
    )
