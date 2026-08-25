"""尋ねる — 実行中 → 答え待ち。

設計: 設計/仕事とは何か.md §6 遷移表・§7「禁止状態」・設計/仕事が回る筋道.md §1。
| 実行中 | 答え待ち | 尋ねる `ask` | `QuestionAsked` | AI |

**判断は求めない**——材料の不足だけ。
相手は `Question` の型が受け持ちの人に縛る。**この仕事の**受け持ちの人であることは
ここが守る——AI が答えやすい人を選んで判断を取りに行けない。
質問の本文は `QuestionAsked` が完載する——正本は出来事（I2 が対で刻ませる）。
**起こす者は担当そのもの**——`by` に担当を入れる。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.job.job import Job, fields_of
from domain.aggregates.job.life import AwaitingAnswer, InProgress
from domain.events.job.question_asked import QuestionAsked
from domain.value_objects.job.question import Question


def ask(
    job: Job[InProgress], question: Question, now: datetime
) -> tuple[Job[AwaitingAnswer], QuestionAsked]:
    """質問を積んで答え待ちへ。返るのは（答え待ちの仕事, 質問された）の対。"""
    if question.to != job.owner:
        raise ValueError("質問の相手は仕事の受け持ちの人だけです（AI が選ばない）")
    asked_by = job.state.assignee
    data = fields_of(job) | {"state": AwaitingAnswer(assignee=asked_by)}
    return Job[AwaitingAnswer].model_validate(data), QuestionAsked(
        at=now, by=asked_by, body=question.body
    )
