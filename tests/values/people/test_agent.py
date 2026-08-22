"""AI の壊しかた。設計/仕事とは何か.md §3。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.values.people.agent import Agent


def test_同じ中身なら等しい() -> None:
    assert Agent(name="一号") == Agent(name="一号")


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        Agent(name="一号").name = "二号"  # type: ignore[misc]


def test_名の空な_AI_は作れない() -> None:
    for text in ("", "   "):
        with pytest.raises(ValidationError):
            Agent(name=text)
