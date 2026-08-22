"""担当の壊しかた。設計/仕事とは何か.md §3。

**人か AI のどちらか。3つ目は無い。**
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain.value_objects.people.agent import Agent
from domain.value_objects.people.assignee import Assignee
from domain.value_objects.people.clock import Clock
from domain.value_objects.people.human import Human

担当 = TypeAdapter(Assignee)


def test_人は担当になれる() -> None:
    assert 担当.validate_python(Human(name="座長")) == Human(name="座長")


def test_AI_は担当になれる() -> None:
    assert 担当.validate_python(Agent(name="一号")) == Agent(name="一号")


def test_時計は担当になれない() -> None:
    with pytest.raises(ValidationError):
        担当.validate_python(Clock())


def test_素の文字列から担当は作れない() -> None:
    with pytest.raises(ValidationError):
        担当.validate_python("座長")
