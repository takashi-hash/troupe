"""打ち切る — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」。
| 打ち切る | `abandon` | 追えなくなった仕事を理由つきで終点へ |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
業務の判断はしない。姿が実行中でも失敗したでもなければ**断りに変えるだけ**。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.services.refusal import Refusal, reason_of
from domain.aggregates.job import abandon as 打ち切り
from domain.aggregates.job.life import Failed, InProgress
from domain.repositories.job_repository import JobRepository
from domain.value_objects.job.job_id import JobId
from domain.value_objects.people.human import Human


def abandon(
    jobs: JobRepository, clock: ClockPort, id: str, by: str, reason: str
) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——一生に傷をつけない。

    **画面から渡るのは文字だけ**（設計 §1）——ui は domain を知らないので、
値に組むのはここ。組めない文字は断りに変わる。
    """
    try:
        鍵, 人 = JobId(text=id), Human(name=by)
    except ValueError as なぜ:
        return Refusal(reason=reason_of(なぜ))
    job = jobs.load(鍵)
    if job is None:
        return Refusal(reason="その仕事はもうありません")
    if not isinstance(job.state, (InProgress, Failed)):
        return Refusal(reason="いまは打ち切れる姿ではありません（もう誰かが動かしました）")
    try:
        next_job, event = 打ち切り.abandon(job, by=人, reason=reason, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=reason_of(なぜ))
    jobs.save(next_job, (event,))
    return None
