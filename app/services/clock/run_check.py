"""検査を回す — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1「時計が始めるもの」・§2「仕様」。
| 検査を回す | `run_check` | 成果の中身を受け入れ基準で見る。**通ったら担当を受け持ちの人へ移す** | **同じ成果なら、いつ回しても同じ結果**（`{対象期間}` は写すときに開かれ済み） |

成果は `ResultStore` から在りかで読む。中身の判定は domain の仕様——ここは運ぶだけ。
在りかの指す成果が置き場に無ければ触らない——読みの食い違いは書きでは直せない。
**何度回しても同じ結果**——検査を回すと提出済みではなくなるので、二度目は拾うものが無い。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.ports.job_state_reader import JobStateReader
from domain.aggregates.job import run_check as 検査
from domain.aggregates.job.life import Submitted
from domain.repositories.job_repository import JobRepository
from domain.repositories.result_store import ResultStore
from domain.value_objects.job.job_id import JobId


def run_check(
    jobs: JobRepository, states: JobStateReader, results: ResultStore, clock: ClockPort
) -> tuple[JobId, ...]:
    """提出済みの成果をぜんぶ受け入れ基準で見て、見た識別子を返す。"""
    now = clock.now()
    checked: list[JobId] = []
    for id in states.ids_in("Submitted"):
        job = jobs.load(id)
        if job is None or not isinstance(job.state, Submitted):
            continue  # もう誰かが動かした——触らない
        if job.result_at is None:
            continue  # 提出済みなら在りかは必ず在る（型の義務）——姿が合わなければ触らない
        result = results.get(job.result_at)
        if result is None:
            continue  # 在りかの指す成果が置き場に無い——触らない
        outcome = 検査.run_check(job, result.body, now)
        jobs.save(outcome[0], outcome[1:])
        checked.append(id)
    return tuple(checked)
