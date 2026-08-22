"""検査を回す — 提出済み → 承認待ち／着手できる／失敗した。

設計: 設計/仕事とは何か.md §6 遷移表・設計/仕事が回る筋道.md §1「時計が始めるもの」・§2「仕様」。
| 提出済み | 承認待ち | 検査を回す `run_check`（通った） | `CheckPassed`（誰へ担当が移ったか） | 時計 |
| 提出済み | 着手できる | 検査を回す `run_check`（止まった・やり直せる） | `CheckStopped`＋`Retried` | 時計 |
| 提出済み | 失敗した | 検査を回す `run_check`（止まった・**やり直しが尽きた**） | `CheckStopped`＋`JobFailed` | 時計 |

中身は仕様（`stop_reason`）——**文字の照合だけ。同じ成果なら、いつ回しても同じ結果**
（`{対象期間}` は写すときに開かれ済み）。
**通ったら担当を受け持ちの人へ移す**——承認待ちの担当の型は `Owner`（I6 の入り口）。
から状態は提出済み1つで、行き先は成果で分かれる——だから返りが union。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import AwaitingApproval, Failed, Ready, Submitted
from domain.events.job.check_passed import CheckPassed
from domain.events.job.check_stopped import CheckStopped
from domain.events.job.job_failed import JobFailed
from domain.events.job.retried import Retried
from domain.services.check import stop_reason
from domain.value_objects.people.clock import Clock


def run_check(
    job: Job[Submitted], result_body: str, now: datetime
) -> (
    tuple[Job[AwaitingApproval], CheckPassed]
    | tuple[Job[Ready], CheckStopped, Retried]
    | tuple[Job[Failed], CheckStopped, JobFailed]
):
    """成果の中身を受け入れ基準で見る。返りはどの道も（次の姿, 出来事…）——I1 が型になる。"""
    by = Clock()
    reason = stop_reason(result_body, job.criteria)
    if reason is None:
        data = fields_of(job) | {"state": AwaitingApproval(assignee=job.owner)}
        return (
            Job[AwaitingApproval].model_validate(data),
            CheckPassed(at=now, by=by, moved_to=job.owner),
        )
    stopped = CheckStopped(at=now, by=by, reason=reason)
    if job.retried < job.max_retries:
        times = job.retried + 1
        data = fields_of(job) | {"state": Ready(), "retried": times}
        return (
            Job[Ready].model_validate(data),
            stopped,
            Retried(at=now, by=by, times=times),
        )
    data = fields_of(job) | {"state": Failed(fallen=reason)}
    return (
        Job[Failed].model_validate(data),
        stopped,
        JobFailed(at=now, by=by, fallen=reason),
    )
