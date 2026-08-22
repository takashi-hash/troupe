"""起こす者の壊しかた。設計/仕事が回る筋道.md §5。

**人・AI・時計の3つのどれか。4つ目は無い。**
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain.value_objects.people.actor import Actor
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.clock import Clock
from domain.value_objects.people.human import Human

起こす者 = TypeAdapter(Actor)


def test_人と_AI_と時計が起こす者になれる() -> None:
    for who in (Human(name="座長"), Agent(name="一号"), Clock()):
        assert 起こす者.validate_python(who) == who


def test_素の文字列から起こす者は作れない() -> None:
    with pytest.raises(ValidationError):
        起こす者.validate_python("時計")


def test_4つ目の起こす者は作れない() -> None:
    """画面は起こす者ではない——開いた人が起こす者。"""
    with pytest.raises(ValidationError):
        起こす者.validate_python({"kind": "screen", "name": "今日"})
