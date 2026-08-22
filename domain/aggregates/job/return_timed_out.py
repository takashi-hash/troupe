"""時間切れを戻す — 実行中 → 着手できる。

設計: 設計/仕事とは何か.md §6 遷移表・設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 実行中 | 着手できる | 時間切れを戻す `return_timed_out` | `JobTimedOut` | 時計 |

**時計が起こす**——時計は引数に取らず、出来事の `by` に `Clock()` を入れる
（domain に時計は置けない。切れているかを見て呼ぶのは呼ぶ側）。
時計は担当にはならないので、外れた担当が「誰の担当だったか」として残る。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import InProgress, Ready
from domain.events.job.job_timed_out import JobTimedOut
from domain.value_objects.people.clock import Clock


def return_timed_out(
    job: Job[InProgress], now: datetime
) -> tuple[Job[Ready], JobTimedOut]:
    """期限の切れた担当を外す。返るのは（着手できる仕事, 時間切れで戻った）の対。"""
    was = job.state.assignee
    data = fields_of(job) | {"state": Ready()}
    return Job[Ready].model_validate(data), JobTimedOut(at=now, by=Clock(), was=was)
