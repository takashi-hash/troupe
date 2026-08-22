"""確かめる — 承認済み・終わった（確かめ待ち）から、終わったか確かめ待ちへ。

設計: 設計/仕事とは何か.md §6 遷移表・不変条件 I5。
| 承認済み | 終わった | 確かめる `confirm`（根拠あり） | `JobFinished` | 時計 |
| 承認済み | 終わった（確かめ待ち） | 確かめる `confirm`（根拠なし） | `JobFinished` | 時計 |
| 終わった（確かめ待ち） | 終わった | 確かめる `confirm`（引用が取れた） | `JobFinished` | 時計 |
| 終わった（確かめ待ち） | 終わった（確かめ待ち） | 確かめる `confirm`（**引用が取れない**） | `RecheckDatePushed` | 時計 |

**時計が起こす**——すべての出来事が `by=Clock()`。源を読み直すのは app の仕事なので、
読めた引用の在りかを引数で受け取る（読めなければ None）。
**から状態で行き先が違う**ので @overload——突合が型注釈を読む。
"""

from __future__ import annotations

from datetime import datetime
from typing import overload

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import Cleared, Finished, FinishedPendingRecheck
from domain.events.job.job_finished import JobFinished
from domain.events.job.recheck_date_pushed import RecheckDatePushed
from domain.value_objects.job.recheck_date import RecheckDate
from domain.value_objects.people.clock import Clock


@overload
def confirm(
    job: Job[Cleared], fetched_evidence_at: str | None, now: datetime
) -> tuple[Job[Finished], JobFinished] | tuple[Job[FinishedPendingRecheck], JobFinished]: ...


@overload
def confirm(
    job: Job[FinishedPendingRecheck], fetched_evidence_at: str | None, now: datetime
) -> (
    tuple[Job[Finished], JobFinished]
    | tuple[Job[FinishedPendingRecheck], RecheckDatePushed]
): ...


def confirm(
    job: Job[Cleared] | Job[FinishedPendingRecheck],
    fetched_evidence_at: str | None,
    now: datetime,
) -> (
    tuple[Job[Finished], JobFinished]
    | tuple[Job[FinishedPendingRecheck], JobFinished]
    | tuple[Job[FinishedPendingRecheck], RecheckDatePushed]
):
    """確かめた結果の（次の姿, 出来事）の対——I1 が型になる。

    承認済みから: 根拠の在りかが空でなければそのまま終わった。読めた引用が
    あれば持たせて終わった。どちらも無ければ確かめ待ちへ——確かめ期日は
    **期日＋写した周期**（AI が決めるのではない）。
    確かめ待ちから: 引用が取れたら終わった。取れなければ**先へ送る**。
    """
    if isinstance(job.state, Cleared):
        evidence_at = job.evidence_at if job.evidence_at is not None else fetched_evidence_at
        if evidence_at is not None:
            data = fields_of(job) | {
                "state": Finished(approval=job.state.approval),
                "evidence_at": evidence_at,
            }
            return Job[Finished].model_validate(data), JobFinished(
                at=now, by=Clock(), evidence_at=evidence_at, recheck_at=None
            )
        recheck = RecheckDate.first(job.due, job.cycle)
        data = fields_of(job) | {
            "state": FinishedPendingRecheck(approval=job.state.approval, recheck=recheck)
        }
        return Job[FinishedPendingRecheck].model_validate(data), JobFinished(
            at=now, by=Clock(), evidence_at=None, recheck_at=recheck.at
        )
    if fetched_evidence_at is not None:
        data = fields_of(job) | {
            "state": Finished(approval=job.state.approval),
            "evidence_at": fetched_evidence_at,
        }
        return Job[Finished].model_validate(data), JobFinished(
            at=now, by=Clock(), evidence_at=fetched_evidence_at, recheck_at=None
        )
    recheck = job.state.recheck.push(job.cycle)
    data = fields_of(job) | {
        "state": FinishedPendingRecheck(approval=job.state.approval, recheck=recheck)
    }
    return Job[FinishedPendingRecheck].model_validate(data), RecheckDatePushed(
        at=now, by=Clock(), recheck_at=recheck.at
    )
