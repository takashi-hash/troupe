"""質問の壊しかた。設計/仕事とは何か.md §3・公理「判断は人間」。

**尋ねるのは材料で、判断ではない。** 相手は受け持ちの人——AI が選ばない。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.job.question import Question
from domain.people.agent import Agent
from domain.people.human import Human
from domain.people.owner import Owner

受け持ちの人 = Owner(person=Human(name="座長"))


def test_中身と相手を持つ質問は作れる() -> None:
    質問 = Question(body="8月分の源はどのフォルダですか", to=受け持ちの人)
    assert 質問.body == "8月分の源はどのフォルダですか"
    assert 質問.to == 受け持ちの人


def test_中身の空な質問は作れない() -> None:
    for text in ("", "   ", "\n\t", "　"):
        with pytest.raises(ValidationError):
            Question(body=text, to=受け持ちの人)


def test_中身の欠けた質問は作れない() -> None:
    with pytest.raises(ValidationError):
        Question(to=受け持ちの人)  # type: ignore[call-arg]


def test_相手の欠けた質問は作れない() -> None:
    with pytest.raises(ValidationError):
        Question(body="8月分の源はどのフォルダですか")  # type: ignore[call-arg]


def test_AI_は質問の相手にならない() -> None:
    with pytest.raises(ValidationError):
        Question(body="8月分の源はどこですか", to=Agent(name="一号"))  # type: ignore[arg-type]


def test_受け持ちの人でない人は質問の相手にならない() -> None:
    with pytest.raises(ValidationError):
        Question(body="8月分の源はどこですか", to=Human(name="通りすがり"))  # type: ignore[arg-type]


def test_名の空な人は受け持ちの人にならないので質問の相手にならない() -> None:
    with pytest.raises(ValidationError):
        Question(body="8月分の源はどこですか", to=Owner(person=Human(name="")))


def test_尋ねたあと書き換えられない() -> None:
    質問 = Question(body="8月分の源はどこですか", to=受け持ちの人)
    with pytest.raises(ValidationError):
        質問.to = Owner(person=Human(name="別の人"))  # type: ignore[misc]
