"""答える — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」・§4。
| 答える | `answer` | 質問に答える。**答えは根拠にならない**——根拠は源から取る |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
回答の本文は `QuestionAnswered` が完載する——正本は出来事。仕事は着手できるへ戻る。
業務の判断はしない。姿が答え待ちでなければ**断りに変えるだけ**——出来事も刻まれない。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.services.refusal import Refusal, reason_of
from domain.aggregates.job import answer as 回答
from domain.aggregates.job.life import AwaitingAnswer
from domain.repositories.job_repository import JobRepository
from domain.value_objects.job.answer import Answer
from domain.value_objects.job.job_id import JobId
from domain.value_objects.people.human import Human


def answer(
    jobs: JobRepository, clock: ClockPort, id: str, by: str, body: str
) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——一生に傷をつけない。

    **画面から渡るのは文字だけ**（設計 §1）——ui は domain を知らないので、
値に組むのはここ。組めない文字は断りに変わる。
    """
    try:
        鍵 = JobId(text=id)
        ans = Answer(by=Human(name=by), body=body)
    except ValueError as なぜ:
        return Refusal(reason=reason_of(なぜ))
    job = jobs.load(鍵)
    if job is None:
        return Refusal(reason="その仕事はもうありません")
    if not isinstance(job.state, AwaitingAnswer):
        return Refusal(reason="いまは答えを待っていません（もう誰かが動かしました）")
    try:
        next_job, event = 回答.answer(job, ans, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=reason_of(なぜ))
    jobs.save(next_job, (event,))
    return None
