"""検査に通ったの壊しかた。設計/仕事が回る筋道.md §5——移る先は受け持ちの人。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.check_passed import CheckPassed
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.clock import Clock
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
受け持ち = Owner(person=Human(name="座長"))


def test_検査に通ったは誰へ担当が移ったかを残す() -> None:
    出来事 = CheckPassed(at=いま, by=Clock(), moved_to=受け持ち)
    assert set(CheckPassed.model_fields) == {"at", "by", "moved_to"}
    assert 出来事.moved_to == 受け持ち


def test_AIへは移れない() -> None:
    """移った先の型が `Owner`——AI へ移った形は書けない。"""
    with pytest.raises(ValidationError):
        CheckPassed(at=いま, by=Clock(), moved_to=Agent(name="番頭"))  # type: ignore[arg-type]
