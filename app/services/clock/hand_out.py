"""配る — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 配る | `hand_out` | 作られた仕事を着手できるへ | 既に配ったものは触らない |

**誰も呼ばなくても回る。何度回しても同じ結果**——配ると作られたではなくなるので、
二度目は拾うものが無い。読みと書きの間に誰かが動かしていても、姿を検めて触らない。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.job_state_reader import JobStateReader
from domain.aggregates.job import hand_out as 配布
from domain.aggregates.job.life import Created
from domain.repositories.job_repository import JobRepository
from domain.value_objects.job.job_id import JobId


def hand_out(
    jobs: JobRepository, states: JobStateReader, clock: ClockPort
) -> tuple[JobId, ...]:
    """作られたをぜんぶ着手できるへ配り、配った識別子を返す。既に配ったものは触らない。"""
    now = clock.now()
    handed: list[JobId] = []
    for id in states.ids_in("Created"):
        job = jobs.load(id)
        if job is None or not isinstance(job.state, Created):
            continue  # 既に配ったものは触らない
        next_job, event = 配布.hand_out(job, now)
        jobs.save(next_job, (event,))
        handed.append(id)
    return tuple(handed)
