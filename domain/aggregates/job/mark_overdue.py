"""期日切れを刻む — 期日を越えた仕事に一度だけ印を残す。**状態は変わらない。**

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」・仕事とは何か.md §6。
| 期日切れを刻む | `mark_overdue` | 期日を越えた仕事に一度だけ印を残す | 日付の比べだけ |

遷移表の外で刻める例外のひとつ（`DueDatePassed`）——
**同じ状態の型を返す関数**として書く。返すのは（同じ状態, 出来事）の対。
**時計が起こす**——`by=Clock()`。期日を過ぎていなければ何も残さない。
終点（終わった・打ち切られた）にも残さない——もう人の手は要らない。
"""

from __future__ import annotations

from datetime import datetime
from typing import TypeVar

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import TERMINAL, StateUnion
from domain.events.job.due_date_passed import DueDatePassed
from domain.value_objects.people.clock import Clock

S = TypeVar("S", bound=StateUnion)


def mark_overdue(job: Job[S], now: datetime) -> tuple[Job[S], DueDatePassed] | None:
    """期日を越えていれば（同じ状態の仕事, 期日を過ぎた）の対。

    越えていなければ None。終点にも None。日付の比べだけ——判断を含まない。
    「一度だけ」は呼び手が既に印のある仕事を呼ばないことで守る。
    """
    if job.state.name in TERMINAL:
        return None
    if now <= job.due.at:
        return None
    return job, DueDatePassed(at=now, by=Clock())
