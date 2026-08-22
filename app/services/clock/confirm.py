"""確かめる — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 確かめる | `confirm` | **根拠の在りかが空でなければ**終わる。空なら源を読み直し、引用が取れれば積んで終わる。取れなければ**確かめ期日を先へ送る** | 積まれた根拠は必ず揃っている（`Evidence` の義務）。**源を読むのでここだけ結果が変わりうる** |

承認済みと確かめ待ちを確かめる。根拠が無ければ `SourcePort` を読み直し、
取れた引用は `EvidenceStore` に積んでから domain の `confirm`。
**確かめ待ちは確かめ期日が来たものだけ読む（実装の決め）**——来る前に読むと、
取れないたびに確かめ期日が先へ送られ、期日が期日でなくなる。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.job_state_reader import JobStateReader
from app.ports.source_port import Quote, SourcePort
from domain.aggregates.job import confirm as 確認
from domain.aggregates.job.life import Cleared, FinishedPendingRecheck
from domain.repositories.evidence_store import EvidenceStore
from domain.repositories.job_repository import JobRepository
from domain.value_objects.job.job_id import JobId


def confirm(
    jobs: JobRepository,
    states: JobStateReader,
    sources: SourcePort,
    evidences: EvidenceStore,
    clock: ClockPort,
) -> tuple[JobId, ...]:
    """承認済みと、確かめ期日の来た確かめ待ちをぜんぶ確かめ、確かめた識別子を返す。"""
    now = clock.now()
    confirmed: list[JobId] = []
    for id in states.ids_in("Cleared") + states.ids_in("FinishedPendingRecheck"):
        job = jobs.load(id)
        if job is None or not isinstance(job.state, (Cleared, FinishedPendingRecheck)):
            continue  # もう誰かが動かした——触らない
        if isinstance(job.state, FinishedPendingRecheck) and now < job.state.recheck.at:
            continue  # 確かめ期日が来ていない——触らない
        fetched: str | None = None
        if job.evidence_at is None:
            outcome = sources.read(job.source)
            if isinstance(outcome, Quote):
                fetched = evidences.put(outcome.evidence)
        next_job, event = 確認.confirm(job, fetched, now)
        jobs.save(next_job, (event,))
        confirmed.append(id)
    return tuple(confirmed)
