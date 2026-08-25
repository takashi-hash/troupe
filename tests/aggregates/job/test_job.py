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
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.job.approval import Approval
from domain.value_objects.job.recheck_date import RecheckDate
from domain.value_objects.job.spent import Spent
from domain.value_objects.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま, 座長


def _approval() -> Approval:
    return Approval(by=座長, at=いま)


def test_業務ルール発は生まれた版と対象期間が三つ揃う() -> None:
    with pytest.raises(ValidationError):
        make_job(Ready(), born_version=None)


def test_作成元が生まれた版と食い違うと作れない() -> None:
    """I3 — 二度作らない鍵が嘘になる形を型で殺す。"""
    from domain.value_objects.job.origin import Origin

    with pytest.raises(ValidationError):
        make_job(Ready(), origin=Origin(key="rule:別のルール/v9/2026-W01"))


def test_訪問仕事の作成元は規則と患者と訪問日の形でしか作れない() -> None:
    """訪問日を持つ仕事の鍵は rule:<規則名>/<患者>/<訪問日>——版と期間は入らない。"""
    from domain.value_objects.job.origin import Origin

    良い鍵 = Origin(key="rule:週次の依存の棚卸し/P-001/2026-08-18")
    make_job(Ready(), origin=良い鍵, visit_date="2026-08-18")  # 通る形
    for 悪い鍵 in (
        "rule:週次の依存の棚卸し/v1/2026-W34/P-001/2026-08-18",  # 版と期間が混ざる(中に/)
        "rule:週次の依存の棚卸し//2026-08-18",                   # 患者が空
        "rule:別のルール/P-001/2026-08-18",                      # 規則が違う
        "rule:週次の依存の棚卸し/P-001/2026-08-19",              # 訪問日が違う
    ):
        with pytest.raises(ValidationError):
            make_job(Ready(), origin=Origin(key=悪い鍵), visit_date="2026-08-18")


def test_開かれていない差し込みを持つ仕事は作れない() -> None:
    from domain.value_objects.rule.criteria import AcceptanceCriteria

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
