"""期日切れを刻む — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 期日切れを刻む | `mark_overdue` | 期日を越えた仕事に一度だけ印を残す | 日付の比べだけ |

**二度目を刻まない工夫はここで決める（実装の決め）: 既に印のある仕事の識別子を
`OverdueMarkReader` で読み、飛ばす。** 印は出来事（`DueDatePassed`）にしか残らず、
仕事の欄には無い——設計に無い欄を足さず、刻んだ事実そのものを照合の材料にする。
この読みは §4 の一覧に無い——「設計に戻す話」。
期日前に刻まない・終点に刻まないのは domain が守る。日付の比べだけ——判断を含まない。
"""

from __future__ import annotations

from typing import Final, Protocol

from app.ports.clock_port import ClockPort
from app.ports.job_state_reader import JobStateReader
from domain.aggregates.job import mark_overdue as 刻印
from domain.aggregates.job.life import STATE_WORDS, TERMINAL
from domain.ledger.job_repository import JobRepository
from domain.values.job.job_id import JobId

#: 印の残りうる状態——終点には刻まない。
_NON_TERMINAL: Final = tuple(n for n in STATE_WORDS.values() if n not in TERMINAL)


class OverdueMarkReader(Protocol):
    """既に「期日を過ぎた」の印が刻まれた仕事の読み。二度目を刻まないための照合の材料。"""

    def marked_ids(self) -> frozenset[JobId]:
        """既に印のある仕事の識別子をぜんぶ。"""
        ...


def mark_overdue(
    jobs: JobRepository,
    states: JobStateReader,
    marks: OverdueMarkReader,
    clock: ClockPort,
) -> tuple[JobId, ...]:
    """期日を越えた仕事に印を残し、刻んだ識別子を返す。既に印のあるものは触らない。"""
    now = clock.now()
    already = marks.marked_ids()
    stamped: list[JobId] = []
    for name in _NON_TERMINAL:
        for id in states.ids_in(name):
            if id in already:
                continue  # 一度だけ——既に印のあるものは触らない
            job = jobs.load(id)
            if job is None:
                continue
            outcome = 刻印.mark_overdue(job, now)
            if outcome is None:
                continue  # 期日を越えていない——触らない
            same, event = outcome
            jobs.save(same, (event,))
            stamped.append(id)
    return tuple(stamped)
