"""仕事の集約のテストが共有する組み立て。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import StateUnion
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.due_date import DueDate
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.origin import Origin
from domain.value_objects.job.spent import Spent
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner
from domain.value_objects.rule.budget import Budget
from domain.value_objects.rule.copied import Copied
from domain.value_objects.rule.criteria import AcceptanceCriteria
from domain.value_objects.rule.instruction import Instruction
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
座長 = Human(name="座長")


def make_job(state: StateUnion, **over: object) -> Job[Any]:
    """週次の依存の棚卸し・版1から生まれた仕事。欄は over で差し替える。"""
    rule = RuleName(text="週次の依存の棚卸し")
    period = Period(text="2026-W34")
    data: dict[str, object] = {
        "id": JobId(text="J-0001"),
        "origin": Origin.from_rule(rule, 1, period),
        "born_of": rule,
        "born_version": 1,
        "period": period,
        "instruction": Instruction(text="依存の一覧を取り更新が来ているものを挙げる"),
        "criteria": AcceptanceCriteria(required_terms=("2026-W34",)),
        "owner": Owner(person=座長),
        "budget": Budget(calls=20, seconds=600),
        "source": Source(location="deps://prod"),
        "cycle": Cycle.WEEKLY,
        "max_retries": 20,
        "due": DueDate.from_start(いま, 3),
        "spent": Spent(calls=0, seconds=0),
        "retried": 0,
        "result_at": None,
        "evidence_at": None,
        "state": state,
    }
    return Job.model_validate(data | over)


def make_copied(**over: object) -> Copied:
    """週次の依存の棚卸し・版1から写した束（受け入れ基準は開かれ済み）。欄は over で差し替える。"""
    data: dict[str, object] = {
        "instruction": Instruction(text="依存の一覧を取り更新が来ているものを挙げる"),
        "criteria": AcceptanceCriteria(required_terms=("2026-W34",)),
        "cycle": Cycle.WEEKLY,
        "owner": Owner(person=座長),
        "budget": Budget(calls=20, seconds=600),
        "source": Source(location="deps://prod"),
        "max_retries": 20,
        "days": 3,
    }
    return Copied.model_validate(data | over)
