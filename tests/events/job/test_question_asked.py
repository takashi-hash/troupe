"""質問されたの壊しかた。設計/仕事が回る筋道.md §5——判断は求めない。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.question_asked import QuestionAsked
from domain.value_objects.people.agent import Agent

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_何を尋ねたかが残る() -> None:
    出来事 = QuestionAsked(at=いま, by=Agent(name="出納係"), body="対象は先月分だけですか")
    assert set(QuestionAsked.model_fields) == {"at", "by", "body"}
    assert 出来事.body == "対象は先月分だけですか"


def test_中身が空なら作れない() -> None:
    with pytest.raises(ValidationError, match="質問の中身"):
        QuestionAsked(at=いま, by=Agent(name="出納係"), body=" ")
