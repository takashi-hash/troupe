"""時間切れを戻す — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 時間切れを戻す | `return_timed_out` | 期限の切れた担当を外す | 切れていないものは触らない |

**期限の線はここで決める（実装の決め）: 担当の期限＝仕事の期日。**
仕事は担当を取った時刻を持たない——仕事自身が持つ締めは期日だけ。
期日を過ぎてなお実行中なら、担当を外して着手できるへ戻す。
**誰も呼ばなくても回る。何度回しても同じ結果**——外すと実行中ではなくなるので、
二度目は拾うものが無い。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.job_state_reader import JobStateReader
from domain.aggregates.job import return_timed_out as 時間切れ
from domain.aggregates.job.life import InProgress
from domain.ledger.job_repository import JobRepository
from domain.values.job.job_id import JobId


def return_timed_out(
    jobs: JobRepository, states: JobStateReader, clock: ClockPort
) -> tuple[JobId, ...]:
    """期限の切れた担当をぜんぶ外し、外した識別子を返す。切れていないものは触らない。"""
    now = clock.now()
    returned: list[JobId] = []
    for id in states.ids_in("InProgress"):
        job = jobs.load(id)
        if job is None or not isinstance(job.state, InProgress):
            continue  # もう誰かが動かした——触らない
        if now <= job.due.at:
            continue  # 切れていないものは触らない
        next_job, event = 時間切れ.return_timed_out(job, now)
        jobs.save(next_job, (event,))
        returned.append(id)
    return tuple(returned)
