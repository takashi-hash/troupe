"""手放す — 実行中 → 着手できる。

設計: 設計/仕事とは何か.md §6 遷移表・設計/仕事が回る筋道.md §1「AI が始めるもの」。
| 実行中 | 着手できる | 手放す `release` | `JobReleased` | 担当 |

**やめる判断ではない。** 担当を外して着手できるへ戻すだけ——誰でもまた取れる。
**起こす者はいまの担当そのもの**なので、引数に受け取らない。
出来事の `by` も、外れた担当も、いまの担当。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import InProgress, Ready
from domain.events.job.job_released import JobReleased


def release(job: Job[InProgress], now: datetime) -> tuple[Job[Ready], JobReleased]:
    """担当を外す。返るのは（着手できる仕事, 手放された）の対——I1 が型になる。"""
    released = job.state.assignee
    data = fields_of(job) | {"state": Ready()}
    return Job[Ready].model_validate(data), JobReleased(
        at=now, by=released, released=released
    )
