"""見立てが書かれたの壊しかた。設計/仕事が回る筋道.md §5——AI が主語だが判断ではない。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.assessment_written import AssessmentWritten
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.people.agent import Agent

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_読んだ中身とそう読んだ理由が残る() -> None:
    見立て = Assessment(
        finding="20回とも同じ理由で落ちている",
        reason="毎回同じ位置で源が読めていない。源の在りかが変わった可能性が高い",
    )
    出来事 = AssessmentWritten(at=いま, by=Agent(name="出納係"), assessment=見立て)
    assert set(AssessmentWritten.model_fields) == {"at", "by", "assessment"}
    assert 出来事.assessment == 見立て


def test_見立てが欠けたら作れない() -> None:
    with pytest.raises(ValidationError):
        AssessmentWritten(at=いま, by=Agent(name="出納係"))  # type: ignore[call-arg]


def test_見立ては素の文字列から作れない() -> None:
    with pytest.raises(ValidationError):
        AssessmentWritten(at=いま, by=Agent(name="出納係"), assessment="読んだだけ")  # type: ignore[arg-type]
