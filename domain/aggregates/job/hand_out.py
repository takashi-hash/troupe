"""配る — 作られた → 着手できる。

設計: 設計/仕事とは何か.md §6 遷移表。
| 作られた | 着手できる | 配る `hand_out` | `JobHandedOut` | 時計 |

**時計が起こす**——誰も呼ばなくても回る。既に配ったものは触らない
（配れるのは `Job[Created]` だけ——引数の型が「から」を言う）。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import Created, Ready
from domain.events.job.job_handed_out import JobHandedOut
from domain.values.people.clock import Clock


def hand_out(job: Job[Created], now: datetime) -> tuple[Job[Ready], JobHandedOut]:
    """着手できるへ出す。返るのは（着手できる仕事, 仕事が配られた）の対——I1 が型になる。"""
    data = fields_of(job) | {"state": Ready()}
    return Job[Ready].model_validate(data), JobHandedOut(at=now, by=Clock())
