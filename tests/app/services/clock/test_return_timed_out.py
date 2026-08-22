"""時間切れを戻す（app）の壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」。

期限の線＝仕事の期日（実装の決め、app/services/clock/return_timed_out.py）。
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.clock.return_timed_out import return_timed_out
from domain.aggregates.job.life import InProgress, Ready
from domain.events.job.job_timed_out import JobTimedOut
from domain.value_objects.job.due_date import DueDate
from domain.value_objects.people.agent import Agent
from tests.aggregates.job.conftest import make_job
from tests.app.services.clock.conftest import 状態の読みの偽物
from tests.app.services.conftest import 固定時計, 帳簿の偽物

働き手 = Agent(name="働き手")
切れた期日 = DueDate.from_start(datetime(2026, 8, 10, 9, 0, tzinfo=UTC), 3)


def test_期日の切れた担当を外して着手できるへ戻す() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=働き手), due=切れた期日)
    帳簿.jobs[仕事.id] = 仕事
    戻った = return_timed_out(帳簿, 状態の読みの偽物(帳簿), 固定時計())
    assert 戻った == (仕事.id,)
    assert isinstance(帳簿.jobs[仕事.id].state, Ready)
    assert len(帳簿.events) == 1
    出来事 = 帳簿.events[0]
    assert isinstance(出来事, JobTimedOut) and 出来事.was == 働き手


def test_切れていないものは触らない() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=働き手))  # 期日は 2026-08-20、いまは 2026-08-18
    帳簿.jobs[仕事.id] = 仕事
    assert return_timed_out(帳簿, 状態の読みの偽物(帳簿), 固定時計()) == ()
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events
