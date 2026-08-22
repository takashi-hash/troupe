"""業務ルールが有効になったの壊しかた。設計/仕事が回る筋道.md §5——人が主語。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.rule.rule_activated import RuleActivated
from domain.value_objects.people.human import Human
from domain.value_objects.rule.rule_name import RuleName

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
名 = RuleName(text="週次の依存の棚卸し")


def test_有効になったは_誰がとどの版かを残す() -> None:
    出来事 = RuleActivated(at=いま, by=Human(name="座長"), rule_name=名, version=2)
    assert set(RuleActivated.model_fields) == {"at", "by", "rule_name", "version"}
    assert 出来事.by == Human(name="座長")
    assert 出来事.rule_name == 名 and 出来事.version == 2


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        RuleActivated(
            at=いま, by=Human(name="座長"), rule_name=名, version=1, 理由="x"  # type: ignore[call-arg]
        )
