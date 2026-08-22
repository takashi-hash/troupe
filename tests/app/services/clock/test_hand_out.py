"""配る（app）の壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」。"""

from __future__ import annotations

from app.services.clock.hand_out import hand_out
from domain.aggregates.job.life import Created, Ready
from domain.events.job.job_handed_out import JobHandedOut
from tests.aggregates.job.conftest import make_job
from tests.app.services.clock.conftest import 状態の読みの偽物
from tests.app.services.conftest import 固定時計, 帳簿の偽物


def test_作られたを着手できるへ配る() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Created())
    帳簿.jobs[仕事.id] = 仕事
    配られた = hand_out(帳簿, 状態の読みの偽物(帳簿), 固定時計())
    assert 配られた == (仕事.id,)
    assert isinstance(帳簿.jobs[仕事.id].state, Ready)
    assert len(帳簿.events) == 1 and isinstance(帳簿.events[0], JobHandedOut)


def test_何度回しても同じ_既に配ったものは触らない() -> None:
    """同じ帳簿に2回回して、2度目は何もしない。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Created())
    帳簿.jobs[仕事.id] = 仕事
    状態の読み = 状態の読みの偽物(帳簿)
    assert hand_out(帳簿, 状態の読み, 固定時計()) == (仕事.id,)
    assert hand_out(帳簿, 状態の読み, 固定時計()) == ()
    assert len(帳簿.events) == 1
