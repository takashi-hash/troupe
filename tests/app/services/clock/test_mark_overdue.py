"""期日切れを刻む（app）の壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」。

二度目を刻まない工夫＝既に印のある仕事を読んで飛ばす
（実装の決め、app/services/clock/mark_overdue.py）。
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.clock.mark_overdue import mark_overdue
from domain.aggregates.job.life import Finished, Ready
from domain.events.job.due_date_passed import DueDatePassed
from domain.values.job.approval import Approval
from domain.values.job.due_date import DueDate
from domain.values.job.job_id import JobId
from tests.aggregates.job.conftest import make_job, 座長
from tests.app.services.clock.conftest import 出来事つき帳簿の偽物, 印の読みの偽物, 状態の読みの偽物
from tests.app.services.conftest import いま, 固定時計

切れた期日 = DueDate.from_start(datetime(2026, 8, 10, 9, 0, tzinfo=UTC), 3)


def test_期日を越えた仕事に印を残す_状態は変わらない() -> None:
    帳簿 = 出来事つき帳簿の偽物()
    仕事 = make_job(Ready(), due=切れた期日)
    帳簿.jobs[仕事.id] = 仕事
    刻んだ = mark_overdue(帳簿, 状態の読みの偽物(帳簿), 印の読みの偽物(帳簿), 固定時計())
    assert 刻んだ == (仕事.id,)
    assert isinstance(帳簿.jobs[仕事.id].state, Ready)  # 印だけ——状態は変わらない
    assert [type(e) for e in 帳簿.events] == [DueDatePassed]


def test_何度回しても同じ_二度目を刻まない() -> None:
    """同じ帳簿に2回回して、2度目は何もしない——一度だけの印。"""
    帳簿 = 出来事つき帳簿の偽物()
    仕事 = make_job(Ready(), due=切れた期日)
    帳簿.jobs[仕事.id] = 仕事
    状態の読み = 状態の読みの偽物(帳簿)
    印の読み = 印の読みの偽物(帳簿)
    assert mark_overdue(帳簿, 状態の読み, 印の読み, 固定時計()) == (仕事.id,)
    assert mark_overdue(帳簿, 状態の読み, 印の読み, 固定時計()) == ()
    assert len(帳簿.events) == 1


def test_期日前と終点には刻まない() -> None:
    帳簿 = 出来事つき帳簿の偽物()
    期日前 = make_job(Ready())  # 期日は 2026-08-20、いまは 2026-08-18
    終点 = make_job(
        Finished(approval=Approval(by=座長, at=いま)),
        id=JobId(text="J-0002"),
        due=切れた期日,
        result_at="result://1",
        evidence_at="evidence://1",
    )
    帳簿.jobs[期日前.id] = 期日前
    帳簿.jobs[終点.id] = 終点
    assert mark_overdue(帳簿, 状態の読みの偽物(帳簿), 印の読みの偽物(帳簿), 固定時計()) == ()
    assert not 帳簿.events
