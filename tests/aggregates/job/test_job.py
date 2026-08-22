"""仕事の集約ルートの壊しかた。設計/仕事とは何か.md §4・I3・I14。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.life import (
    Cleared,
    Finished,
    FinishedPendingRecheck,
    Ready,
    Submitted,
)
from domain.values.calendar.cycle import Cycle
from domain.values.job.approval import Approval
from domain.values.job.recheck_date import RecheckDate
from domain.values.job.spent import Spent
from domain.values.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま, 座長


def _approval() -> Approval:
    return Approval(by=座長, at=いま)


def test_業務ルール発は生まれた版と対象期間が三つ揃う() -> None:
    with pytest.raises(ValidationError):
        make_job(Ready(), born_version=None)


def test_作成元が生まれた版と食い違うと作れない() -> None:
    """I3 — 二度作らない鍵が嘘になる形を型で殺す。"""
    from domain.values.job.origin import Origin

    with pytest.raises(ValidationError):
        make_job(Ready(), origin=Origin(key="rule:別のルール/v9/2026-W01"))


def test_開かれていない差し込みを持つ仕事は作れない() -> None:
    from domain.values.rule.criteria import AcceptanceCriteria

    with pytest.raises(ValidationError):
        make_job(Ready(), criteria=AcceptanceCriteria(required_terms=("{対象期間}",)))


def test_使った量の上限は積む操作が守る() -> None:
    """I14 の守る場所は `spend`（設計 §5）。帳簿の再構成にきょうの規則を効かせない
    ——「効かせるのは型の形だけ」——ので、集約ルートでは検めない。"""
    仕事 = make_job(Ready(), spent=Spent(calls=21, seconds=0))
    assert not 仕事.spent.within(仕事.budget)


def test_やり直しの上限は負になれない() -> None:
    with pytest.raises(ValidationError):
        make_job(Ready(), max_retries=-1)


def test_成果の在りかの無い提出済みは書けない() -> None:
    with pytest.raises(ValidationError):
        make_job(Submitted(assignee=Agent(name="一号")))


def test_根拠の在りかの無い終わったは書けない() -> None:
    with pytest.raises(ValidationError):
        make_job(Finished(approval=_approval()))


def test_確かめ待ちは根拠の在りかを持てない() -> None:
    recheck = RecheckDate(after=いま, at=いま + Cycle.WEEKLY.span)
    with pytest.raises(ValidationError):
        make_job(
            FinishedPendingRecheck(approval=_approval(), recheck=recheck),
            evidence_at="evidence://1",
        )


def test_やり直した回数は負になれない() -> None:
    with pytest.raises(ValidationError):
        make_job(Ready(), retried=-1)


def test_正しい仕事は作れる() -> None:
    仕事 = make_job(Ready())
    assert 仕事.state == Ready()
    assert 仕事.retried == 0 and 仕事.result_at is None
