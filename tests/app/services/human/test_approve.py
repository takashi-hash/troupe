"""承認する（app）の壊しかた。設計/仕事が回る筋道.md §1・人に見えるもの §3。"""

from __future__ import annotations

from typing import Any

from app.services.human.approve import approve
from domain.aggregates.job.job import Job
from domain.aggregates.job.life import AwaitingApproval, Cleared, Ready
from domain.values.people.human import Human
from domain.values.people.owner import Owner
from tests.aggregates.job.conftest import make_job, 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物


def _帳簿と仕事() -> tuple[帳簿の偽物, Job[Any]]:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(AwaitingApproval(assignee=Owner(person=座長)), result_at="result://1")
    帳簿.jobs[仕事.id] = 仕事
    return 帳簿, 仕事


def test_読んで_承認して_対で書く() -> None:
    帳簿, 仕事 = _帳簿と仕事()
    断り = approve(帳簿, 固定時計(), 仕事.id, by=座長)
    assert 断り is None
    assert isinstance(帳簿.jobs[仕事.id].state, Cleared)
    assert len(帳簿.events) == 1


def test_承認待ちでなければ断りに変わる() -> None:
    """操作の失敗はエラーではない——状態は変わらず、理由だけが返る。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Ready())
    帳簿.jobs[仕事.id] = 仕事
    断り = approve(帳簿, 固定時計(), 仕事.id, by=座長)
    assert 断り is not None and "承認を待っていません" in 断り.reason
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events


def test_受け持ちの人でなければ断りに変わる() -> None:
    帳簿, 仕事 = _帳簿と仕事()
    断り = approve(帳簿, 固定時計(), 仕事.id, by=Human(name="別の人"))
    assert 断り is not None and "受け持ちの人" in 断り.reason
    assert not 帳簿.events


def test_無い仕事は断りに変わる() -> None:
    from domain.values.job.job_id import JobId

    断り = approve(帳簿の偽物(), 固定時計(), JobId(text="J-9999"), by=座長)
    assert 断り is not None
