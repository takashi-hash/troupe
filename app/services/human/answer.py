"""答える — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」・§4。
| 答える | `answer` | 質問に答える。**答えは根拠にならない**——根拠は源から取る |
| `QuestionStore` | Store | 質問と回答を積む | domain | adapters | 積む: `ask`・`answer` |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
回答は質問の在りか（答え待ちの姿が持つ）へ紐づけて積み、仕事は着手できるへ戻る。
業務の判断はしない。姿が答え待ちでなければ**断りに変えるだけ**——回答も積まれない。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.services.refusal import Refusal
from domain.aggregates.job import answer as 回答
from domain.aggregates.job.life import AwaitingAnswer
from domain.repositories.job_repository import JobRepository
from domain.repositories.question_store import QuestionStore
from domain.value_objects.job.answer import Answer
from domain.value_objects.job.job_id import JobId


def answer(
    jobs: JobRepository, questions: QuestionStore, clock: ClockPort, id: JobId, ans: Answer
) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——一生に傷をつけない。"""
    job = jobs.load(id)
    if job is None:
        return Refusal(reason="その仕事はもうありません")
    if not isinstance(job.state, AwaitingAnswer):
        return Refusal(reason="いまは答えを待っていません（もう誰かが動かしました）")
    try:
        next_job, event = 回答.answer(job, ans, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=str(なぜ))
    questions.put_answer(job.state.question_at, ans)
    jobs.save(next_job, (event,))
    return None
