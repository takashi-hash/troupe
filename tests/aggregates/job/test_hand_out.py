"""配るの壊しかた。設計/仕事とは何か.md §6 遷移表・I1。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.hand_out import hand_out
from domain.aggregates.job.life import Created, Ready
from domain.events.job.job_handed_out import JobHandedOut
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.clock import Clock
from tests.aggregates.job.conftest import make_job, いま


def test_作られたから着手できるへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = hand_out(make_job(Created()), いま)
    assert isinstance(仕事.state, Ready)
    assert isinstance(出来事, JobHandedOut) and 出来事.by == Clock() and 出来事.at == いま


def test_配られた仕事は持ちものを引き継ぐ() -> None:
    元 = make_job(Created())
    仕事, _ = hand_out(元, いま)
    assert 仕事.id == 元.id and 仕事.origin == 元.origin and 仕事.due == 元.due


def test_作られたに担当が無い() -> None:
    """型が拒む——担当の欄そのものが無いので、配る前に担当が居る形が書けない。"""
    assert "assignee" not in Created.model_fields
    with pytest.raises(ValidationError):
        Created(assignee=Agent(name="一号"))  # type: ignore[call-arg]


def test_配られても担当も承認も付かない() -> None:
    """着手できるは担当も承認も持ってはいけない——欄が無いから書けない。"""
    仕事, _ = hand_out(make_job(Created()), いま)
    assert isinstance(仕事.state, Ready)
    assert "assignee" not in Ready.model_fields and "approval" not in Ready.model_fields
