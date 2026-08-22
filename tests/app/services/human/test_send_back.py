"""差し戻す（app）の壊しかた。設計/仕事が回る筋道.md §1・人に見えるもの §3。"""

from __future__ import annotations

from app.services.human.send_back import send_back
from domain.aggregates.job.life import AwaitingApproval, Failed, Ready
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.send_back import SendBack
from domain.value_objects.job.spent import Spent
from domain.value_objects.people.owner import Owner
from tests.aggregates.job.conftest import make_job, 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物


def test_読んで_差し戻して_対で書く() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(AwaitingApproval(assignee=Owner(person=座長)), result_at="result://1")
    帳簿.jobs[仕事.id] = 仕事
    断り = send_back(帳簿, 固定時計(), 仕事.id.text, by=座長.name, reason="根拠が古い")
    assert 断り is None
    次 = 帳簿.jobs[仕事.id]
    assert isinstance(次.state, Ready)
    assert 次.spent == Spent(calls=0, seconds=0) and 次.retried == 0
    assert len(帳簿.events) == 1


def test_失敗したからも戻せる() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Failed(fallen="源が読めなかった"), spent=Spent(calls=3, seconds=40), retried=2)
    帳簿.jobs[仕事.id] = 仕事
    断り = send_back(帳簿, 固定時計(), 仕事.id.text, by=座長.name, reason="もう一度")
    assert 断り is None and isinstance(帳簿.jobs[仕事.id].state, Ready)


def test_4つのどれでもなければ断りに変わる() -> None:
    """操作の失敗はエラーではない——状態は変わらず、理由だけが返る。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Ready())
    帳簿.jobs[仕事.id] = 仕事
    断り = send_back(帳簿, 固定時計(), 仕事.id.text, by=座長.name, reason="戻して")
    assert 断り is not None and "差し戻せる姿" in 断り.reason
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events


def test_無い仕事は断りに変わる() -> None:
    断り = send_back(帳簿の偽物(), 固定時計(), "J-9999", by=座長.name, reason="戻して")
    assert 断り is not None
