"""承認する — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」。
| 承認する | `approve` | 差し出した承認を渡す。**受け持ちの人だけ**（I6） |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
業務の判断はしない。`if` で業務を判断したくなったら domain の仕様へ。
姿の検めは「行けない遷移は型が作らせない」の裏返しで、**断りに変えるだけ**。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.services.refusal import Refusal
from domain.aggregates.job import approve as 承認
from domain.aggregates.job.life import AwaitingApproval
from domain.ledger.job_repository import JobRepository
from domain.values.job.job_id import JobId
from domain.values.people.human import Human


def approve(jobs: JobRepository, clock: ClockPort, id: JobId, by: Human) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——一生に傷をつけない。"""
    job = jobs.load(id)
    if job is None:
        return Refusal(reason="その仕事はもうありません")
    if not isinstance(job.state, AwaitingApproval):
        return Refusal(reason="いまは承認を待っていません（もう誰かが動かしました）")
    try:
        next_job, event = 承認.approve(job, by=by, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=str(なぜ))
    jobs.save(next_job, (event,))
    return None
