"""回答の壊しかた。設計/仕事とは何か.md §3・I7。

**答えた人と中身を持つ。** 答えは根拠にならない——根拠は源から取る。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.values.job.answer import Answer
from domain.values.people.agent import Agent
from domain.values.people.human import Human

答えた人 = Human(name="座長")


def test_答えた人と中身を持つ回答は作れる() -> None:
    回答 = Answer(by=答えた人, body="8月分の源は mail/請求 です")
    assert 回答.by == 答えた人
    assert 回答.body == "8月分の源は mail/請求 です"


def test_答えた人の欠けた回答は作れない() -> None:
    with pytest.raises(ValidationError):
        Answer(body="8月分の源は mail/請求 です")  # type: ignore[call-arg]


def test_中身の欠けた回答は作れない() -> None:
    with pytest.raises(ValidationError):
        Answer(by=答えた人)  # type: ignore[call-arg]


def test_中身の空な回答は作れない() -> None:
    for text in ("", "   ", "\n\t", "　"):
        with pytest.raises(ValidationError):
            Answer(by=答えた人, body=text)


def test_名の空な人は答えられない() -> None:
    with pytest.raises(ValidationError):
        Answer(by=Human(name=""), body="8月分の源は mail/請求 です")


def test_AI_は答えられない() -> None:
    with pytest.raises(ValidationError):
        Answer(by=Agent(name="一号"), body="8月分の源は mail/請求 です")  # type: ignore[arg-type]


def test_回答は根拠の欄を持たない() -> None:
    with pytest.raises(ValidationError):
        Answer(
            by=答えた人,
            body="8月分の源は mail/請求 です",
            evidence="mail/請求 から読んだ引用",  # type: ignore[call-arg]
        )


def test_答えたあと書き換えられない() -> None:
    回答 = Answer(by=答えた人, body="8月分の源は mail/請求 です")
    with pytest.raises(ValidationError):
        回答.body = "やっぱり別の場所です"  # type: ignore[misc]
