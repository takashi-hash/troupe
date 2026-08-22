"""受け持ちの人の壊しかた。設計/仕事とは何か.md §3・I6。

**公理「判断は人間」が、ここで型になる。**
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.people.agent import Agent
from domain.people.clock import Clock
from domain.people.human import Human
from domain.people.owner import Owner


def test_人は受け持ちの人になれる() -> None:
    assert Owner(person=Human(name="座長")).person == Human(name="座長")


def test_AI_を受け持ちの人にできない() -> None:
    with pytest.raises(ValidationError):
        Owner(person=Agent(name="一号"))  # type: ignore[arg-type]


def test_時計を受け持ちの人にできない() -> None:
    with pytest.raises(ValidationError):
        Owner(person=Clock())  # type: ignore[arg-type]


def test_名の空な人は受け持ちの人にできない() -> None:
    with pytest.raises(ValidationError):
        Owner(person=Human(name=""))
