"""業務ルールの集約のテストが共有する組み立て。"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.aggregates.rule.rule import Rule
from domain.values.calendar.cycle import Cycle
from domain.values.people.human import Human
from domain.values.people.owner import Owner
from domain.values.rule.budget import Budget
from domain.values.rule.criteria import AcceptanceCriteria
from domain.values.rule.instruction import Instruction
from domain.values.rule.rule_name import RuleName
from domain.values.rule.source import Source
from domain.values.rule.version import Version

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
座長 = Human(name="座長")
名 = RuleName(text="週次の依存の棚卸し")


def make_version(number: int = 1, **over: object) -> Version:
    """週次の依存の棚卸しの版。欄は over で差し替える。"""
    data: dict[str, object] = {
        "number": number,
        "instruction": Instruction(text="依存の一覧を取り更新が来ているものを挙げる"),
        "criteria": AcceptanceCriteria(required_terms=("{対象期間}",)),
        "cycle": Cycle.WEEKLY,
        "days": 3,
        "budget": Budget(calls=20, seconds=600),
        "owner": Owner(person=座長),
        "source": Source(location="deps://prod"),
        "max_retries": 20,
    }
    return Version.model_validate(data | over)


def make_rule(**over: object) -> Rule:
    """版1だけ・まだ無効の業務ルール。欄は over で差し替える。"""
    data: dict[str, object] = {
        "name": 名,
        "versions": (make_version(1),),
        "active": None,
        "activated_by": None,
        "activated_at": None,
    }
    return Rule.model_validate(data | over)
