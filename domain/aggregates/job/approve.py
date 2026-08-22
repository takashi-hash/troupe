"""承認する — 承認待ち → 承認済み。

設計: 設計/仕事とは何か.md §6 遷移表・不変条件 I6・I7。
| 承認待ち | 承認済み | 承認する `approve` | `Approved` | **人**（受け持ちの人） |

**人しか起こせない**（I7 公理の執行者）——`by` の型が `Human` なので、
AI がこの手を呼ぶ行は型検査が赤にする。
**承認できるのは受け持ちの人だけ**（I6）——ここが守る場所。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import AwaitingApproval, Cleared
from domain.events.job.approved import Approved
from domain.values.job.approval import Approval
from domain.values.people.human import Human


def approve(
    job: Job[AwaitingApproval], by: Human, now: datetime
) -> tuple[Job[Cleared], Approved]:
    """承認を渡す。返るのは（承認済みの仕事, 承認された）の対——I1 が型になる。"""
    if by != job.owner.person:
        raise ValueError("承認できるのは受け持ちの人だけです（I6）")
    approval = Approval(by=by, at=now)
    data = fields_of(job) | {"state": Cleared(approval=approval)}
    return Job[Cleared].model_validate(data), Approved(at=now, by=by)
