"""着手する — AI が始めるもの。1つ目の見に来る先。

設計: 設計/仕事が回る筋道.md §1「AI が始めるもの」。
**引き金は AI 自身。常駐して、2つを見に来る。**
| 着手する | `start` | 着手できる仕事を取り、**やること・受け入れ基準・答えのある質問**を揃えて実行中へ | 取れるかは型が決める |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
一覧は `JobStateReader` から——Repository は鍵で1件、一覧と絞り込みは Reader。
姿が合わなければ断りに変えるだけ——エラーは投げない、状態は変えない。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.job_state_reader import JobStateReader
from app.services.refusal import Refusal
from domain.aggregates.job import start as 着手
from domain.aggregates.job.life import Ready
from domain.ledger.job_repository import JobRepository
from domain.values.job.job_id import JobId
from domain.values.people.agent import Agent


def take(
    jobs: JobRepository, states: JobStateReader, clock: ClockPort, by: Agent
) -> JobId | Refusal:
    """着手できるを1件取り、実行中へ。取れたら識別子、取れなければ断り。"""
    ids = states.ids_in("Ready")
    if not ids:
        return Refusal(reason="いま着手できる仕事がありません")
    job = jobs.load(ids[0])
    if job is None:
        return Refusal(reason="その仕事はもうありません")
    if not isinstance(job.state, Ready):
        return Refusal(reason="いまは着手できません（もう誰かが動かしました）")
    next_job, event = 着手.start(job, by=by, now=clock.now())
    jobs.save(next_job, (event,))
    return next_job.id
