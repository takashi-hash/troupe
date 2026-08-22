"""人へ回すの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I15。

**実行中からは `JobFailed` も刻み、失敗したからは刻まない。**
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.hand_over import hand_over
from domain.aggregates.job.job import Job
from domain.aggregates.job.life import Failed, InProgress
from domain.events.job.assessment_written import AssessmentWritten
from domain.events.job.job_failed import JobFailed
from domain.values.job.assessment import Assessment
from domain.values.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま

働き手 = Agent(name="一号")
見立て = Assessment(
    finding="20回とも同じ理由で落ちた。源の在りかが変わった可能性が高い",
    reason="止まった理由の列が全件同一",
)


def test_実行中からは見立てと落ちたが両方刻まれる() -> None:
    """落ちた中身には見立ての本文（finding）をそのまま置く。"""
    仕事, 書かれた, 落ちた = hand_over(
        make_job(InProgress(assignee=働き手)), 見立て, by=働き手, now=いま
    )
    assert isinstance(仕事.state, Failed) and 仕事.state.fallen == 見立て.finding
    assert isinstance(書かれた, AssessmentWritten) and 書かれた.assessment == 見立て
    assert isinstance(落ちた, JobFailed) and 落ちた.fallen == 見立て.finding
    assert 書かれた.by == 働き手 and 落ちた.by == 働き手 and 書かれた.at == いま


def test_失敗したからは見立てだけ_JobFailedは刻まない() -> None:
    """状態は失敗したのまま、落ちた中身も変わらない。"""
    元: Job[Failed] = make_job(Failed(fallen="使用上限に達した"))
    結果 = hand_over(元, 見立て, by=働き手, now=いま)
    assert len(結果) == 2
    仕事, 書かれた = 結果
    assert 仕事 == 元 and 仕事.state == Failed(fallen="使用上限に達した")
    assert isinstance(書かれた, AssessmentWritten) and 書かれた.assessment == 見立て


def test_壊しかた_刻んだ落ちた中身は書き換えられない() -> None:
    仕事, _, _ = hand_over(make_job(InProgress(assignee=働き手)), 見立て, by=働き手, now=いま)
    with pytest.raises(ValidationError):
        仕事.state.fallen = "書き換え"  # type: ignore[misc]
