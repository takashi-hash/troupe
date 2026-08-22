"""差し戻す — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」。
| 差し戻す | `send_back` | 理由をつけて着手できるへ戻す |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
業務の判断はしない。姿が4つ（承認待ち・実行中・失敗した・終わった（確かめ待ち））の
どれでもなければ**断りに変えるだけ**。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.services.refusal import Refusal
from domain.aggregates.job import send_back as 差し戻し
from domain.aggregates.job.life import (
    AwaitingApproval,
    Failed,
    FinishedPendingRecheck,
    InProgress,
)
from domain.ledger.job_repository import JobRepository
from domain.values.job.job_id import JobId
from domain.values.job.send_back import SendBack


def send_back(jobs: JobRepository, clock: ClockPort, id: JobId, sb: SendBack) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——一生に傷をつけない。"""
    job = jobs.load(id)
    if job is None:
        return Refusal(reason="その仕事はもうありません")
    if not isinstance(job.state, (AwaitingApproval, InProgress, Failed, FinishedPendingRecheck)):
        return Refusal(reason="いまは差し戻せる姿ではありません（もう誰かが動かしました）")
    try:
        next_job, event = 差し戻し.send_back(job, sb, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=str(なぜ))
    jobs.save(next_job, (event,))
    return None
