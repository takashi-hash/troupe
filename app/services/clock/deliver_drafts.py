"""下書きを配達する — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 下書きを配達する | `deliver_drafts` | 承認の済んだカルテの下書きを診療録へ
**draft としてだけ**置く | 承認は済んでいる。運ぶだけ——**同じ仕事から二度置かない**
（診療録の一意の鍵） |

配達するのは**カルテの下書きの仕事だけ**——源がカルテ抽出（`db:chart/<患者記号>`）の
仕事。どの患者かは源の在りかが知っている（仕事が生まれたとき版から写したもの）。
帳簿には書かない——書く先は診療録の下書き受けで、置けたかは診療録の鍵が決める。
"""

from __future__ import annotations

from app.ports.emr_draft_port import EmrDraftPort
from app.ports.job_state_reader import JobStateReader
from domain.aggregates.job.life import Cleared, Finished, FinishedPendingRecheck
from domain.repositories.job_repository import JobRepository
from domain.repositories.result_store import ResultStore
from domain.value_objects.job.job_id import JobId

#: カルテ抽出の在りかの形。ここから患者記号が読める。
_CHART = "db:chart/"


def deliver_drafts(
    jobs: JobRepository,
    states: JobStateReader,
    results: ResultStore,
    drafts: EmrDraftPort,
) -> tuple[JobId, ...]:
    """承認の済んだカルテの下書きを配達し、新しく置けた仕事の識別子を返す。"""
    delivered: list[JobId] = []
    for state_name in ("Cleared", "FinishedPendingRecheck", "Finished"):
        for id in states.ids_in(state_name):
            job = jobs.load(id)
            if job is None or not isinstance(
                job.state, (Cleared, FinishedPendingRecheck, Finished)
            ):
                continue  # もう誰かが動かした——触らない
            if not job.source.location.startswith(_CHART):
                continue  # カルテの下書きの仕事ではない
            if job.result_at is None:
                continue
            result = results.get(job.result_at)
            if result is None:
                continue
            if drafts.deposit(id.text, job.source.location.removeprefix(_CHART), result.body):
                delivered.append(id)
    return tuple(delivered)
