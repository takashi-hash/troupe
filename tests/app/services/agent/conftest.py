"""AI のアプリケーションサービスのテストが共有する偽物。

**偽物は宣言（Protocol）を満たす最小の実装**——注ぎ口が本当に注げることの証明でもある。
"""

from __future__ import annotations

from app.ports.source_port import Material, Quote, Unreadable
from app.ports.work_reader import WorkMaterial
from domain.values.job.answer import Answer
from domain.values.job.assessment import Assessment
from domain.values.job.evidence import Evidence
from domain.values.job.job_id import JobId
from domain.values.job.question import Question
from domain.values.job.reply import Reply
from domain.values.job.result import Result
from domain.values.people.agent import Agent
from domain.values.rule.source import Source

働き手 = Agent(name="働き手")


class LLMの偽物:
    """決めた `Reply` と使った量を返す。渡った材料を覚える。"""

    def __init__(self, reply: Reply, calls: int = 1, seconds: int = 5) -> None:
        self.reply = reply
        self.calls = calls
        self.seconds = seconds
        self.received: list[str] = []

    def consult(
        self,
        instruction: str,
        criteria_terms: tuple[str, ...],
        criteria_note: str,
        source_material: str,
        answered_questions: tuple[tuple[str, str], ...],
        previous_result: str | None,
    ) -> tuple[Reply, int, int]:
        self.received.append(source_material)
        return self.reply, self.calls, self.seconds


class 源の偽物:
    """材料／引用／読めない、を並べた順に返す。尽きたら最後を繰り返す。"""

    def __init__(self, *outcomes: Material | Quote | Unreadable) -> None:
        self.outcomes = outcomes
        self.reads = 0

    def read(self, source: Source) -> Material | Quote | Unreadable:
        outcome = self.outcomes[min(self.reads, len(self.outcomes) - 1)]
        self.reads += 1
        return outcome


class 質問置き場の偽物:
    def __init__(self) -> None:
        self.rows: dict[str, tuple[Question, Answer | None]] = {}

    def put_question(self, q: Question) -> str:
        at = f"q://{len(self.rows) + 1}"
        self.rows[at] = (q, None)
        return at

    def put_answer(self, question_at: str, a: Answer) -> None:
        q, _ = self.rows[question_at]
        self.rows[question_at] = (q, a)

    def get(self, at: str) -> tuple[Question, Answer | None] | None:
        return self.rows.get(at)


class 成果置き場の偽物:
    def __init__(self) -> None:
        self.rows: dict[str, Result] = {}

    def put(self, result: Result) -> str:
        at = f"result://{len(self.rows) + 1}"
        self.rows[at] = result
        return at

    def get(self, at: str) -> Result | None:
        return self.rows.get(at)


class 根拠置き場の偽物:
    def __init__(self) -> None:
        self.rows: dict[str, Evidence] = {}

    def put(self, evidence: Evidence) -> str:
        at = f"evidence://{len(self.rows) + 1}"
        self.rows[at] = evidence
        return at

    def get(self, at: str) -> Evidence | None:
        return self.rows.get(at)


class 見立て置き場の偽物:
    def __init__(self) -> None:
        self.rows: list[tuple[JobId, Assessment]] = []

    def put(self, job: JobId, a: Assessment) -> str:
        self.rows.append((job, a))
        return f"assessment://{len(self.rows)}"

    def list_for(self, job: JobId) -> tuple[Assessment, ...]:
        return tuple(a for j, a in self.rows if j == job)


class 状態読みの偽物:
    def __init__(self, ids: dict[str, tuple[JobId, ...]] | None = None) -> None:
        self.ids = ids or {}

    def ids_in(self, state_name: str, assignee_name: str | None = None) -> tuple[JobId, ...]:
        return self.ids.get(state_name, ())


class 材料読みの偽物:
    def __init__(self, material: WorkMaterial | None = None) -> None:
        self.material = material or WorkMaterial(
            answered_questions=(),
            previous_result=None,
            fall_reasons=(),
            assessments=(),
            sibling_states=(),
        )

    def read(self, id: JobId) -> WorkMaterial:
        return self.material
