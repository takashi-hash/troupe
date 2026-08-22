"""使い切るの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I14。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.exhaust import EXHAUSTED, exhaust
from domain.aggregates.job.life import Failed, InProgress
from domain.events.job.job_failed import JobFailed
from domain.value_objects.job.spent import Spent
from domain.value_objects.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま

働き手 = Agent(name="一号")


def test_実行中から失敗したへ_落ちた中身は使用上限に達した() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対。`spend` が I14 で止めた直後の姿から。"""
    元 = make_job(InProgress(assignee=働き手), spent=Spent(calls=20, seconds=600))
    仕事, 出来事 = exhaust(元, now=いま)
    assert isinstance(仕事.state, Failed) and 仕事.state.fallen == EXHAUSTED
    assert isinstance(出来事, JobFailed) and 出来事.fallen == EXHAUSTED
    assert 出来事.by == 働き手 and 出来事.at == いま


def test_使い切った量はそのまま引き継がれる() -> None:
    元 = make_job(InProgress(assignee=働き手), spent=Spent(calls=20, seconds=600))
    仕事, _ = exhaust(元, now=いま)
    assert 仕事.spent == Spent(calls=20, seconds=600) and 仕事.id == 元.id


def test_壊しかた_落ちた中身を後から書き換えられない() -> None:
    仕事, _ = exhaust(make_job(InProgress(assignee=働き手)), now=いま)
    with pytest.raises(ValidationError):
        仕事.state.fallen = "書き換え"  # type: ignore[misc]
