"""アプリケーションサービスのテストが共有する偽物。

**偽物は宣言（Protocol）を満たす最小の実装**——注ぎ口が本当に注げることの証明でもある。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from domain.aggregates.job.job import Job
from domain.aggregates.rule.rule import Rule
from domain.events.event import Event
from domain.values.job.answer import Answer
from domain.values.job.job_id import JobId
from domain.values.job.question import Question
from domain.values.rule.copied import Copied
from domain.values.rule.rule_name import RuleName

いま = datetime(2026, 8, 18, 9, 2, tzinfo=UTC)


class 固定時計:
    def now(self) -> datetime:
        return いま


class 帳簿の偽物:
    """メモリの上の JobRepository。書き込みの門の形（対でしか積めない）は本物と同じ。"""

    def __init__(self) -> None:
        self.jobs: dict[JobId, Job[Any]] = {}
        self.events: list[Event] = []

    def load(self, id: JobId) -> Job[Any] | None:
        return self.jobs.get(id)

    def save(self, job: Job[Any], events: tuple[Event, ...]) -> None:
        assert events, "出来事なしの書き込み（I1 違反）"
        self.jobs[job.id] = job
        self.events.extend(events)


class ルール帳簿の偽物:
    """メモリの上の RuleRepository。書き込みの門の形（対でしか積めない）は本物と同じ。"""

    def __init__(self) -> None:
        self.rules: dict[RuleName, Rule] = {}
        self.events: list[Event] = []

    def load(self, name: RuleName) -> Rule | None:
        return self.rules.get(name)

    def save(self, rule: Rule, events: tuple[Event, ...]) -> None:
        assert events, "出来事なしの書き込み（I2 違反）"
        self.rules[rule.name] = rule
        self.events.extend(events)


class 連番の識別子:
    """メモリの上の IdPort。呼ばれるたび新しい識別子を1つ振る。"""

    def __init__(self) -> None:
        self.count = 0

    def new_id(self) -> str:
        self.count += 1
        return f"ID-{self.count:04d}"


class 質問置き場の偽物:
    """メモリの上の QuestionStore。積むと在りかが返る形は本物と同じ。"""

    def __init__(self) -> None:
        self.questions: dict[str, Question] = {}
        self.answers: dict[str, Answer] = {}

    def put_question(self, q: Question) -> str:
        at = f"question://{len(self.questions) + 1}"
        self.questions[at] = q
        return at

    def put_answer(self, question_at: str, a: Answer) -> None:
        self.answers[question_at] = a

    def get(self, at: str) -> tuple[Question, Answer | None] | None:
        q = self.questions.get(at)
        return None if q is None else (q, self.answers.get(at))


class 題材の偽物:
    """メモリの上の TopicPort。渡された束を初期値としてそのまま返す。"""

    def __init__(self, copied: Copied | None = None) -> None:
        self.copied = copied

    def read(self, rule: RuleName) -> Copied | None:
        return self.copied
