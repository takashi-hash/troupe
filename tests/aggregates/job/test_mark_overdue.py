"""期日切れを刻むの壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」・仕事とは何か.md §6。"""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from domain.aggregates.job.life import Abandoned, Finished, InProgress
from domain.aggregates.job.mark_overdue import mark_overdue
from domain.events.job.due_date_passed import DueDatePassed
from domain.value_objects.job.approval import Approval
from domain.value_objects.job.due_date import DueDate
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.clock import Clock
from tests.aggregates.job.conftest import make_job, いま, 座長

期日 = DueDate.from_start(いま, 3)
過ぎたいま = 期日.at + timedelta(hours=1)


def test_期日を過ぎたら同じ状態のまま印が残る() -> None:
    """状態は変わらない——返るのは（同じ状態の仕事, 期日を過ぎた）の対。"""
    元 = make_job(InProgress(assignee=Agent(name="一号")))
    組 = mark_overdue(元, 過ぎたいま)
    assert 組 is not None
    仕事, 出来事 = 組
    assert 仕事 == 元 and isinstance(仕事.state, InProgress)
    assert isinstance(出来事, DueDatePassed)
    assert 出来事.by == Clock() and 出来事.at == 過ぎたいま


def test_期日を過ぎていなければ何も残らない() -> None:
    """期日ちょうども過ぎていない——日付の比べだけ。"""
    元 = make_job(InProgress(assignee=Agent(name="一号")))
    assert mark_overdue(元, いま) is None
    assert mark_overdue(元, 期日.at) is None


def test_終点には残らない() -> None:
    """終わった・打ち切られたには、もう人の手は要らない。"""
    終わった = make_job(
        Finished(approval=Approval(by=座長, at=いま)),
        result_at="result://1",
        evidence_at="evidence://1",
    )
    打ち切られた = make_job(Abandoned(by=座長, reason="源が消えた"))
    assert mark_overdue(終わった, 過ぎたいま) is None
    assert mark_overdue(打ち切られた, 過ぎたいま) is None


def test_起こす者は素の文字列から作れない() -> None:
    """型が拒む——期日を過ぎたの起こす者は人・AI・時計のどれか。"""
    with pytest.raises(ValidationError):
        DueDatePassed(at=いま, by="clock")  # type: ignore[arg-type]
