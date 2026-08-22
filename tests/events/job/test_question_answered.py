"""答えられたの壊しかた。設計/仕事が回る筋道.md §5——人が主語。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.question_answered import QuestionAnswered
from domain.values.people.agent import Agent
from domain.values.people.human import Human

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
座長 = Human(name="座長")


def test_誰が何と答え_誰の担当が外れたかが残る() -> None:
    出来事 = QuestionAnswered(
        at=いま, by=座長, body="先月の分だけでよい", unassigned=Agent(name="出納係")
    )
    assert set(QuestionAnswered.model_fields) == {"at", "by", "body", "unassigned"}
    assert 出来事.by == 座長
    assert 出来事.body == "先月の分だけでよい"
    assert 出来事.unassigned == Agent(name="出納係")


def test_答えの中身が空なら作れない() -> None:
    with pytest.raises(ValidationError, match="答えの中身"):
        QuestionAnswered(at=いま, by=座長, body=" ", unassigned=Agent(name="出納係"))


def test_外れた担当は素の文字列から作れない() -> None:
    with pytest.raises(ValidationError):
        QuestionAnswered(at=いま, by=座長, body="x", unassigned="出納係")  # type: ignore[arg-type]
