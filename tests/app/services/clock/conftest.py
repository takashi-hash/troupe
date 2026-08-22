"""時計のアプリケーションサービスのテストが共有する偽物と組み立て。

**偽物は宣言（Protocol）を満たす最小の実装**——注ぎ口が本当に注げることの証明でもある。
読みの偽物は帳簿の偽物から導く——本物の adapters と同じ向き（読みは帳簿の写し）。
だから同じ帳簿に2回回す試験で、2度目が1度目の書き込みをちゃんと見る。
"""

from __future__ import annotations

from typing import Any

from app.ports.source_port import SourceOutcome
from domain.aggregates.job.job import Job
from domain.aggregates.rule.rule import Rule
from domain.events.event import Event
from domain.events.job.due_date_passed import DueDatePassed
from domain.values.calendar.cycle import Cycle
from domain.values.job.evidence import Evidence
from domain.values.job.job_id import JobId
from domain.values.job.result import Result
from domain.values.people.owner import Owner
from domain.values.rule.budget import Budget
from domain.values.rule.criteria import AcceptanceCriteria
from domain.values.rule.instruction import Instruction
from domain.values.rule.rule_name import RuleName
from domain.values.rule.source import Source
from domain.values.rule.version import Version
from tests.aggregates.job.conftest import 座長
from tests.app.services.conftest import いま, 帳簿の偽物


def make_rule(**over: object) -> Rule:
    """週次の依存の棚卸し・版1が有効な業務ルール。受け入れ基準に `{対象期間}` の穴。"""
    version = Version(
        number=1,
        instruction=Instruction(text="依存の一覧を取り更新が来ているものを挙げる"),
        criteria=AcceptanceCriteria(required_terms=("{対象期間}",)),
        cycle=Cycle.WEEKLY,
        days=3,
        budget=Budget(calls=20, seconds=600),
        owner=Owner(person=座長),
        source=Source(location="deps://prod"),
        max_retries=20,
    )
    data: dict[str, object] = {
        "name": RuleName(text="週次の依存の棚卸し"),
        "versions": (version,),
        "active": 1,
        "activated_by": 座長,
        "activated_at": いま,
    }
    return Rule.model_validate(data | over)


class 規則帳簿の偽物:
    """メモリの上の RuleRepository。書き込みの門の形（対でしか積めない）は本物と同じ。"""

    def __init__(self) -> None:
        self.rules: dict[RuleName, Rule] = {}

    def load(self, name: RuleName) -> Rule | None:
        return self.rules.get(name)

    def save(self, rule: Rule, events: tuple[Event, ...]) -> None:
        assert events, "出来事なしの書き込み（I2 違反）"
        self.rules[rule.name] = rule


class 有効版の読みの偽物:
    """規則帳簿の偽物から導く ActiveRuleReader。"""

    def __init__(self, rules: 規則帳簿の偽物) -> None:
        self._rules = rules

    def read_all(self) -> tuple[tuple[RuleName, int, Cycle], ...]:
        out: list[tuple[RuleName, int, Cycle]] = []
        for rule in self._rules.rules.values():
            if rule.active is None:
                continue
            version = next(v for v in rule.versions if v.number == rule.active)
            out.append((rule.name, version.number, version.cycle))
        return tuple(out)


class 作成元の読みの偽物:
    """帳簿の偽物から導く OriginReader。"""

    def __init__(self, ledger: 帳簿の偽物) -> None:
        self._ledger = ledger

    def keys(self) -> frozenset[str]:
        return frozenset(job.origin.key for job in self._ledger.jobs.values())


class 状態の読みの偽物:
    """帳簿の偽物から導く JobStateReader。"""

    def __init__(self, ledger: 帳簿の偽物) -> None:
        self._ledger = ledger

    def ids_in(self, state_name: str, assignee_name: str | None = None) -> tuple[JobId, ...]:
        return tuple(
            id for id, job in self._ledger.jobs.items() if job.state.name == state_name
        )


class 採番の偽物:
    """連番の IdPort。"""

    def __init__(self) -> None:
        self._count = 0

    def new_id(self) -> str:
        self._count += 1
        return f"J-{self._count:04d}"


class 成果置き場の偽物:
    """メモリの上の ResultStore。積むと在りかが返る。"""

    def __init__(self) -> None:
        self.items: dict[str, Result] = {}

    def put(self, result: Result) -> str:
        at = f"result://{len(self.items) + 1}"
        self.items[at] = result
        return at

    def get(self, at: str) -> Result | None:
        return self.items.get(at)


class 根拠置き場の偽物:
    """メモリの上の EvidenceStore。積むと在りかが返る。"""

    def __init__(self) -> None:
        self.items: dict[str, Evidence] = {}

    def put(self, evidence: Evidence) -> str:
        at = f"evidence://{len(self.items) + 1}"
        self.items[at] = evidence
        return at

    def get(self, at: str) -> Evidence | None:
        return self.items.get(at)


class 源の偽物:
    """決めた出口をいつも返す SourcePort。読んだ回数を数える。"""

    def __init__(self, outcome: SourceOutcome) -> None:
        self.outcome = outcome
        self.reads = 0

    def read(self, source: Source) -> SourceOutcome:
        self.reads += 1
        return self.outcome


class 出来事つき帳簿の偽物(帳簿の偽物):
    """仕事ごとの出来事も持つ帳簿の偽物——印の読みの材料。"""

    def __init__(self) -> None:
        super().__init__()
        self.by_job: dict[JobId, list[Event]] = {}

    def save(self, job: Job[Any], events: tuple[Event, ...]) -> None:
        super().save(job, events)
        self.by_job.setdefault(job.id, []).extend(events)


class 印の読みの偽物:
    """出来事つき帳簿の偽物から導く OverdueMarkReader。"""

    def __init__(self, ledger: 出来事つき帳簿の偽物) -> None:
        self._ledger = ledger

    def marked_ids(self) -> frozenset[JobId]:
        return frozenset(
            id
            for id, events in self._ledger.by_job.items()
            if any(isinstance(e, DueDatePassed) for e in events)
        )
