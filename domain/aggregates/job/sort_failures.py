"""失敗を仕分ける — 失敗した → 着手できる、または残す。

設計: 設計/仕事とは何か.md §6 遷移表・仕事が回る筋道.md §1「時計が始めるもの」。
| 失敗した | 着手できる | 失敗を仕分ける `sort_failures` | `Retried` | 時計 |
| 失敗を仕分ける | `sort_failures` | **やり直した回数が上限に届かず、使った量が使用上限に届かなければ**やり直す。どちらか届けば残す | 比べるだけ。**4つとも仕事が持つ**——Store に尋ねない |

**時計が起こす**——判断ではない。比べるだけ。
どちらか届いていれば None（残す——遷移しない）。
残った仕事に見立てを付けるのは AI の巡回（I15）、決めるのは人（差し戻すか打ち切るか）。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import Failed, Ready
from domain.events.job.retried import Retried
from domain.value_objects.people.clock import Clock


def sort_failures(
    job: Job[Failed], now: datetime
) -> tuple[Job[Ready], Retried] | None:
    """届いていなければやり直し（回数+1）、どちらか届いていれば残す。

    やり直すときの返りは（着手できる仕事, もう一度やった）の対——I1 が型になる。
    """
    if job.retried >= job.max_retries:
        return None
    if job.spent.calls >= job.budget.calls or job.spent.seconds >= job.budget.seconds:
        return None
    times = job.retried + 1
    data = fields_of(job) | {"state": Ready(), "retried": times}
    return Job[Ready].model_validate(data), Retried(at=now, by=Clock(), times=times)
