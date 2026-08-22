"""失敗を仕分ける（app）の壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」。"""

from __future__ import annotations

from app.services.clock.sort_failures import sort_failures
from domain.aggregates.job.life import Failed, Ready
from domain.events.job.retried import Retried
from tests.aggregates.job.conftest import make_job
from tests.app.services.clock.conftest import 状態の読みの偽物
from tests.app.services.conftest import 固定時計, 帳簿の偽物


def test_どちらも届いていなければやり直しに出す() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Failed(fallen="必ず含む語がありません: 2026-W34"))  # 0/20 回・0/20 呼び
    帳簿.jobs[仕事.id] = 仕事
    出した = sort_failures(帳簿, 状態の読みの偽物(帳簿), 固定時計())
    assert 出した == (仕事.id,)
    assert isinstance(帳簿.jobs[仕事.id].state, Ready)
    assert 帳簿.jobs[仕事.id].retried == 1
    assert [type(e) for e in 帳簿.events] == [Retried]


def test_やり直しが尽きていれば残す() -> None:
    """残す＝触らない。残った仕事に見立てを付けるのは AI、決めるのは人。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Failed(fallen="必ず含む語がありません: 2026-W34"), retried=20)  # 上限 20
    帳簿.jobs[仕事.id] = 仕事
    assert sort_failures(帳簿, 状態の読みの偽物(帳簿), 固定時計()) == ()
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events
