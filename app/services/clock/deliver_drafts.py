"""下書きを配達する — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」。
| 下書きを配達する | `deliver_drafts` | 承認の済んだカルテの下書きを**その訪問
（患者・訪問日）宛て**に診療録へ **draft としてだけ**置く。置けたら
**`DraftDelivered` を刻む**——配達は帳簿に残る事実（F4）
| 承認は済んでいる。運ぶだけ——**印の無いものだけ運ぶ**（診療録の一意の鍵は二重の守り） |

配達するのは**カルテの下書きの仕事だけ**——源がカルテ抽出（`db:chart/<患者記号>`）の
仕事。どの患者かは源の在りかが、どの訪問宛てかは仕事の訪問日が知っている
（どちらも仕事が生まれたとき写したもの）。訪問日の無い仕事は宛先が無い——運ばない。

**印が正本。** 帳簿が配達を覚えているから、毎分の脈は印の無いものしか見ないし、
診療録の種を入れ直しても二度目は運ばれない。届かなかったら刻まない——次の脈がまた来る。
置いてから刻む——刻んでから置き損ねると、二度と運ばれない下書きができる。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.delivered_mark_reader import DeliveredMarkReader
from app.ports.emr_draft_port import EmrDraftPort
from app.ports.job_state_reader import JobStateReader
from domain.aggregates.job import deliver_drafts as 配達
from domain.repositories.job_repository import JobRepository
from domain.repositories.result_store import ResultStore
from domain.value_objects.job.job_id import JobId

#: カルテ抽出の在りかの形。ここから患者記号が読める。
_CHART = "db:chart/"


def deliver_drafts(
    jobs: JobRepository,
    states: JobStateReader,
    results: ResultStore,
    marks: DeliveredMarkReader,
    drafts: EmrDraftPort,
    clock: ClockPort,
) -> tuple[JobId, ...]:
    """印の無い、承認の済んだカルテの下書きを配達し、刻んだ仕事の識別子を返す。"""
    now = clock.now()
    既に = marks.marked_ids()
    delivered: list[JobId] = []
    for state_name in ("Cleared", "FinishedPendingRecheck", "Finished"):
        for id in states.ids_in(state_name):
            if id in 既に:
                continue  # 帳簿が覚えている——二度目は運ばない
            job = jobs.load(id)
            if job is None or not job.source.location.startswith(_CHART):
                continue  # カルテの下書きの仕事ではない
            if job.visit_date is None:
                continue  # 宛先の訪問が無い——旧い形の仕事。運ばない
            対 = 配達.deliver_drafts(job, now)
            if 対 is None:
                continue  # 承認を経ていない・成果が無い——配達の事実になれない
            result = results.get(job.result_at) if job.result_at else None
            if result is None:
                continue
            if not drafts.deposit(id.text, job.source.location.removeprefix(_CHART),
                                  job.visit_date, result.body):
                continue  # 診療録に届かなかった——刻まず、次の脈がまた来る
            next_job, event = 対
            try:
                jobs.save(next_job, (event,))
            except RuntimeError:
                continue  # 誰かが先に書いた（AI の脈の見立てなど）——次の脈がまた来る
            delivered.append(id)
    return tuple(delivered)
