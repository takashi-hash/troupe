"""見立てを書くの壊しかた。設計/仕事が回る筋道.md §1「AI が始めるもの」・I13。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.assess import assess
from domain.aggregates.job.life import Failed, Finished, InProgress
from domain.events.job.assessment_written import AssessmentWritten
from domain.values.job.approval import Approval
from domain.values.job.assessment import Assessment
from domain.values.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま, 座長

一号 = Agent(name="一号")
見立て = Assessment(
    finding="20回とも同じ理由で落ちた", reason="源の在りかが変わった可能性が高い"
)


def test_見立てを書いても状態が変わらない() -> None:
    """状態は変わらない——返るのは（同じ状態の仕事, 見立てが書かれた）の対。"""
    元 = make_job(Failed(fallen="源が読めない"))
    仕事, 出来事 = assess(元, 見立て, by=一号, now=いま)
    assert 仕事 == 元 and isinstance(仕事.state, Failed)
    assert isinstance(出来事, AssessmentWritten)
    assert 出来事.assessment == 見立て and 出来事.by == 一号 and 出来事.at == いま


def test_担当でなくても書ける() -> None:
    """I13 の例外——見立てを書くのは、姿を変えることではない。"""
    元 = make_job(InProgress(assignee=一号))
    仕事, 出来事 = assess(元, 見立て, by=Agent(name="二号"), now=いま)
    assert 仕事 == 元 and 出来事.by == Agent(name="二号")


def test_終わった仕事にも書ける() -> None:
    """落ちた仕事・終わった仕事こそ見立てが要る。"""
    元 = make_job(
        Finished(approval=Approval(by=座長, at=いま)),
        result_at="result://1",
        evidence_at="evidence://1",
    )
    仕事, 出来事 = assess(元, 見立て, by=一号, now=いま)
    assert 仕事 == 元 and isinstance(仕事.state, Finished)
    assert isinstance(出来事, AssessmentWritten)


def test_理由の無い見立てが作れない() -> None:
    """型が拒む——見立ては読んだ結果と、そう読んだ理由を両方持つ。"""
    with pytest.raises(ValidationError):
        Assessment(finding="落ちている", reason="")
