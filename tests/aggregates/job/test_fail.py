"""落ちるの壊しかた。設計/仕事とは何か.md §6 遷移表・I1。"""

from __future__ import annotations

import pytest

from domain.aggregates.job.fail import fail
from domain.aggregates.job.life import Failed, InProgress
from domain.events.job.job_failed import JobFailed
from domain.value_objects.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま

働き手 = Agent(name="一号")


def test_実行中から失敗したへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = fail(make_job(InProgress(assignee=働き手)), fallen="源が読めない", now=いま)
    assert isinstance(仕事.state, Failed) and 仕事.state.fallen == "源が読めない"
    assert isinstance(出来事, JobFailed) and 出来事.fallen == "源が読めない"
    assert 出来事.by == 働き手 and 出来事.at == いま


def test_落ちた姿は担当を持たない() -> None:
    """失敗したには担当の欄そのものが無い。"""
    仕事, _ = fail(make_job(InProgress(assignee=働き手)), fallen="源が読めない", now=いま)
    assert "assignee" not in type(仕事.state).model_fields


def test_壊しかた_空の落ちた中身では落ちられない() -> None:
    with pytest.raises(ValueError, match="落ちた中身"):
        fail(make_job(InProgress(assignee=働き手)), fallen="   ", now=いま)
