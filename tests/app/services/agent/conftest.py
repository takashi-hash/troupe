"""AI のアプリケーションサービスのテストが共有する偽物。

**偽物は宣言（Protocol）を満たす最小の実装**——注ぎ口が本当に注げることの証明でもある。
"""

from __future__ import annotations

from app.ports.source_port import Quote, Unreadable
from app.ports.work_reader import WorkMaterial
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.reply import Reply
from domain.value_objects.job.result import Result
from domain.value_objects.people.agent import Agent
from domain.value_objects.rule.source import Source

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

    def read_situation(
        self,
        situation: str,
        fall_reasons: tuple[str, ...],
        previous_result: str | None,
        sibling_states: tuple[str, ...],
    ) -> tuple[str, str, int, int]:
        raise AssertionError("この筋書きで巡回の見立ては書かれない")

class 源の偽物:
    """材料／引用／読めない、を並べた順に返す。尽きたら最後を繰り返す。"""

    def __init__(self, *outcomes: Quote | Unreadable) -> None:
        self.outcomes = outcomes
        self.reads = 0

    def read(self, source: Source) -> Quote | Unreadable:
        outcome = self.outcomes[min(self.reads, len(self.outcomes) - 1)]
        self.reads += 1
        return outcome


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
