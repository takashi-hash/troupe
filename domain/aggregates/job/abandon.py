"""打ち切る — 実行中・失敗した → 打ち切られた。

設計: 設計/仕事とは何か.md §6 遷移表・不変条件 I1・I7。
| 実行中 | 打ち切られた | 打ち切る `abandon` | `JobAbandoned` | **人**（見立てを読んで） |
| 失敗した | 打ち切られた | 打ち切る `abandon` | `JobAbandoned` | **人** |

**人しか起こせない**（I7 公理の執行者）——`by` の型が `Human` なので、
AI がこの手を呼ぶ行は型検査が赤にする。
**終点。** 打ち切った人と理由が状態に残る。ここから出る遷移は無い。
行き先はどちらも「打ち切られた」なので引数を union にする（overload は行き先が違うときだけ）。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import Abandoned, Failed, InProgress
from domain.events.job.job_abandoned import JobAbandoned
from domain.values.people.human import Human


def abandon(
    job: Job[InProgress] | Job[Failed], by: Human, reason: str, now: datetime
) -> tuple[Job[Abandoned], JobAbandoned]:
    """追えなくなった仕事を理由つきで終点へ。返るのは（打ち切られた仕事, 打ち切られた）の対——I1 が型になる。"""
    data = fields_of(job) | {"state": Abandoned(by=by, reason=reason)}
    return Job[Abandoned].model_validate(data), JobAbandoned(at=now, by=by, reason=reason)
