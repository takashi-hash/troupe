"""業務ルールが止められたの壊しかた。設計/仕事が回る筋道.md §5——人が主語。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import get_type_hints

import pytest
from pydantic import ValidationError

from domain.events.rule.rule_deactivated import RuleDeactivated
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.human import Human
from domain.value_objects.rule.rule_name import RuleName

いま = datetime(2026, 8, 22, 10, 0, tzinfo=UTC)
名 = RuleName(text="壊れた棚卸し")


def test_どの版を止めたかが残る() -> None:
    出来事 = RuleDeactivated(at=いま, by=Human(name="座長"), rule_name=名, version=1)
    assert 出来事.rule_name == 名 and 出来事.version == 1


def test_AIは止められない() -> None:
    """止めるのも判断——太字（人が主語）が型になる（I7）。"""
    assert get_type_hints(RuleDeactivated)["by"] is Human
    with pytest.raises(ValidationError):
        RuleDeactivated(at=いま, by=Agent(name="一号"), rule_name=名, version=1)  # type: ignore[arg-type]
