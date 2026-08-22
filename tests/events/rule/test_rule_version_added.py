"""版が足されたの壊しかた。設計/仕事が回る筋道.md §5。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.rule.rule_version_added import RuleVersionAdded
from domain.values.people.human import Human
from domain.values.rule.rule_name import RuleName

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
名 = RuleName(text="週次の依存の棚卸し")


def test_版が足されたは_どの版かを足して残す() -> None:
    出来事 = RuleVersionAdded(at=いま, by=Human(name="座長"), rule_name=名, version=1)
    assert set(RuleVersionAdded.model_fields) == {"at", "by", "rule_name", "version"}
    assert 出来事.rule_name == 名 and 出来事.version == 1


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        RuleVersionAdded(
            at=いま, by=Human(name="座長"), rule_name=名, version=1, 中身="x"  # type: ignore[call-arg]
        )
