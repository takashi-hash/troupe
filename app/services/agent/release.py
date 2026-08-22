"""手放す — AI が始めるもの。

設計: 設計/仕事が回る筋道.md §1「AI が始めるもの」。
| 手放す | `release` | 担当を外して着手できるへ | やめる判断ではない |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
起こす者はいまの担当そのものなので、引数に受け取らない。
姿が合わなければ断りに変えるだけ——エラーは投げない、状態は変えない。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.services.refusal import Refusal
from domain.aggregates.job import release as 手放す
from domain.aggregates.job.life import InProgress
from domain.ledger.job_repository import JobRepository
from domain.values.job.job_id import JobId


def release(jobs: JobRepository, clock: ClockPort, id: JobId) -> Refusal | None:
    """通れば None。断られたら理由。"""
    job = jobs.load(id)
    if job is None:
        return Refusal(reason="その仕事はもうありません")
    if not isinstance(job.state, InProgress):
        return Refusal(reason="いまは実行中ではありません（手放すものがありません）")
    next_job, event = 手放す.release(job, now=clock.now())
    jobs.save(next_job, (event,))
    return None
