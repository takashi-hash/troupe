"""手放す（app）の壊しかた。設計/仕事が回る筋道.md §1「AI が始めるもの」。"""

from __future__ import annotations

from app.services.agent.release import release
from domain.aggregates.job.life import Ready, InProgress
from domain.events.job.job_released import JobReleased
from tests.aggregates.job.conftest import make_job
from tests.app.services.conftest import 固定時計, 帳簿の偽物
from tests.app.services.agent.conftest import 働き手


def test_担当を外して着手できるへ() -> None:
    """やめる判断ではない——誰でもまた取れる形に戻すだけ。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=働き手))
    帳簿.jobs[仕事.id] = 仕事
    断り = release(帳簿, 固定時計(), 仕事.id)
    assert 断り is None
    assert isinstance(帳簿.jobs[仕事.id].state, Ready)
    assert [type(e) for e in 帳簿.events] == [JobReleased]


def test_実行中でなければ断りに変わる() -> None:
    """操作の失敗はエラーではない——状態は変わらず、理由だけが返る。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Ready())
    帳簿.jobs[仕事.id] = 仕事
    断り = release(帳簿, 固定時計(), 仕事.id)
    assert 断り is not None and "実行中ではありません" in 断り.reason
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events


def test_無い仕事は断りに変わる() -> None:
    from domain.value_objects.job.job_id import JobId

    断り = release(帳簿の偽物(), 固定時計(), JobId(text="J-9999"))
    assert 断り is not None
