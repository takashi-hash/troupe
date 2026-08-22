"""失敗を仕分ける — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 失敗を仕分ける | `sort_failures` | **やり直した回数が上限に届かず、使った量が使用上限に届かなければ**やり直す。どちらか届けば残す | 比べるだけ。**4つとも仕事が持つ**——Store に尋ねない |

比べるのは domain——ここは運ぶだけ。domain が None を返したら残す（触らない）。
残った仕事に見立てを付けるのは AI の巡回、決めるのは人（差し戻すか打ち切るか）。
**何度回しても同じ結果**——やり直すと失敗したではなくなり、残すものは何度見ても残る。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.job_state_reader import JobStateReader
from domain.aggregates.job import sort_failures as 仕分け
from domain.aggregates.job.life import Failed
from domain.ledger.job_repository import JobRepository
from domain.values.job.job_id import JobId


def sort_failures(
    jobs: JobRepository, states: JobStateReader, clock: ClockPort
) -> tuple[JobId, ...]:
    """失敗したをぜんぶ仕分け、やり直しに出した識別子を返す。残すものは触らない。"""
    now = clock.now()
    retried: list[JobId] = []
    for id in states.ids_in("Failed"):
        job = jobs.load(id)
        if job is None or not isinstance(job.state, Failed):
            continue  # もう誰かが動かした——触らない
        outcome = 仕分け.sort_failures(job, now)
        if outcome is None:
            continue  # どちらか届いた——残す（触らない）
        next_job, event = outcome
        jobs.save(next_job, (event,))
        retried.append(id)
    return tuple(retried)
