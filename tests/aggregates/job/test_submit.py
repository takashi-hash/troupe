"""出すの壊しかた。設計/仕事とは何か.md §6 遷移表・I1。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import InProgress, Submitted
from domain.aggregates.job.submit import submit
from domain.events.job.result_submitted import ResultSubmitted
from domain.values.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま

一号 = Agent(name="一号")


def _in_progress() -> Job[InProgress]:
    return make_job(InProgress(assignee=一号))


def test_実行中から提出済みへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = submit(_in_progress(), result_at="result://1", evidence_at=None, now=いま)
    assert isinstance(仕事.state, Submitted) and 仕事.state.assignee == 一号
    assert 仕事.result_at == "result://1" and 仕事.evidence_at is None
    assert isinstance(出来事, ResultSubmitted) and 出来事.by == 一号 and 出来事.at == いま
    assert 出来事.result_at == "result://1" and 出来事.evidence_at is None


def test_引用が取れたときは根拠の在りかも一緒に持つ() -> None:
    仕事, 出来事 = submit(
        _in_progress(), result_at="result://1", evidence_at="evidence://1", now=いま
    )
    assert 仕事.evidence_at == "evidence://1"
    assert 出来事.evidence_at == "evidence://1"


def test_提出済みの仕事は持ちものを引き継ぐ() -> None:
    元 = _in_progress()
    仕事, _ = submit(元, result_at="result://1", evidence_at=None, now=いま)
    assert 仕事.id == 元.id and 仕事.origin == 元.origin
    assert 仕事.spent == 元.spent and 仕事.retried == 元.retried


def test_成果の在りかの無い提出は仕事の義務が拒む() -> None:
    """提出済みは成果の在りかが空でない——型が str と言い、義務が None を拒む。"""
    with pytest.raises(ValidationError):
        submit(_in_progress(), result_at=None, evidence_at=None, now=いま)  # type: ignore[arg-type]
