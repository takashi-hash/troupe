"""質問と回答の置き場の宣言の壊しかた。設計/仕事が回る筋道.md §4。

宣言は Protocol——実装の義務はここで言い切り、実装のテストが同じ検査を通る。
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from domain.ledger.question_store import QuestionStore
from domain.values.job.answer import Answer
from domain.values.job.question import Question


def test_質問を積むと在りかが返る() -> None:
    """Store の積むは在りかを返す——振る者と積む者を2つにしない。"""
    hints = get_type_hints(QuestionStore.put_question)
    assert hints["q"] == Question
    assert hints["return"] is str
    params = list(inspect.signature(QuestionStore.put_question).parameters)
    assert params == ["self", "q"]


def test_回答は質問の在りかへ紐づけて積む() -> None:
    """回答だけが宙に浮く形が書けない。"""
    hints = get_type_hints(QuestionStore.put_answer)
    assert hints["question_at"] is str
    assert hints["a"] == Answer
    assert hints["return"] is type(None)
    params = list(inspect.signature(QuestionStore.put_answer).parameters)
    assert params == ["self", "question_at", "a"]


def test_読みは在りかで質問と回答の対() -> None:
    hints = get_type_hints(QuestionStore.get)
    assert hints["return"] == tuple[Question, Answer | None] | None
    params = list(inspect.signature(QuestionStore.get).parameters)
    assert params == ["self", "at"]
