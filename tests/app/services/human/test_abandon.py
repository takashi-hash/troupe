"""打ち切る（app）の壊しかた。設計/仕事が回る筋道.md §1・人に見えるもの §3。"""

from __future__ import annotations

from app.services.human.abandon import abandon
from domain.aggregates.job.life import Abandoned, Failed, InProgress, Ready
from domain.values.job.job_id import JobId
from domain.values.people.agent import Agent
from tests.aggregates.job.conftest import make_job, 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物

一号 = Agent(name="一号")


def test_読んで_打ち切って_対で書く() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=一号))
    帳簿.jobs[仕事.id] = 仕事
    断り = abandon(帳簿, 固定時計(), 仕事.id, by=座長, reason="源が消えた")
    assert 断り is None
    assert isinstance(帳簿.jobs[仕事.id].state, Abandoned)
    assert len(帳簿.events) == 1


def test_失敗したからも打ち切れる() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Failed(fallen="やり直しが尽きた"))
    帳簿.jobs[仕事.id] = 仕事
    assert abandon(帳簿, 固定時計(), 仕事.id, by=座長, reason="追えない") is None
    assert isinstance(帳簿.jobs[仕事.id].state, Abandoned)


def test_実行中でも失敗したでもなければ断りに変わる() -> None:
    """操作の失敗はエラーではない——状態は変わらず、理由だけが返る。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Ready())
    帳簿.jobs[仕事.id] = 仕事
    断り = abandon(帳簿, 固定時計(), 仕事.id, by=座長, reason="やめたい")
    assert 断り is not None and "打ち切れる姿" in 断り.reason
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events


def test_理由が空なら断りに変わる() -> None:
    """理由なしの打ち切りは義務が拒む——エラーではなく断りが返る。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=一号))
    帳簿.jobs[仕事.id] = 仕事
    断り = abandon(帳簿, 固定時計(), 仕事.id, by=座長, reason=" ")
    assert 断り is not None and not 帳簿.events


def test_無い仕事は断りに変わる() -> None:
    断り = abandon(帳簿の偽物(), 固定時計(), JobId(text="J-9999"), by=座長, reason="追えない")
    assert 断り is not None
