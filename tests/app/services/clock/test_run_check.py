"""検査を回す（app）の壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」・§2「仕様」。"""

from __future__ import annotations

from app.services.clock.run_check import run_check
from domain.aggregates.job.life import AwaitingApproval, Ready, Submitted
from domain.events.job.check_passed import CheckPassed
from domain.events.job.check_stopped import CheckStopped
from domain.events.job.retried import Retried
from domain.value_objects.job.result import Result
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.owner import Owner
from tests.aggregates.job.conftest import make_job, 座長
from tests.app.services.clock.conftest import 成果置き場の偽物, 状態の読みの偽物
from tests.app.services.conftest import 固定時計, 帳簿の偽物

働き手 = Agent(name="働き手")


def test_通れば承認待ちへ_担当は受け持ちの人へ移る() -> None:
    帳簿 = 帳簿の偽物()
    置き場 = 成果置き場の偽物()
    在りか = 置き場.put(Result(body="2026-W34 の依存はぜんぶ最新"))
    仕事 = make_job(Submitted(assignee=働き手), result_at=在りか)
    帳簿.jobs[仕事.id] = 仕事
    見た = run_check(帳簿, 状態の読みの偽物(帳簿), 置き場, 固定時計())
    assert 見た == (仕事.id,)
    状態 = 帳簿.jobs[仕事.id].state
    assert isinstance(状態, AwaitingApproval) and 状態.assignee == Owner(person=座長)
    assert [type(e) for e in 帳簿.events] == [CheckPassed]


def test_止まればやり直しに出す() -> None:
    帳簿 = 帳簿の偽物()
    置き場 = 成果置き場の偽物()
    在りか = 置き場.put(Result(body="依存は最新"))  # 必ず含む語 2026-W34 が無い
    仕事 = make_job(Submitted(assignee=働き手), result_at=在りか)
    帳簿.jobs[仕事.id] = 仕事
    見た = run_check(帳簿, 状態の読みの偽物(帳簿), 置き場, 固定時計())
    assert 見た == (仕事.id,)
    assert isinstance(帳簿.jobs[仕事.id].state, Ready)
    assert 帳簿.jobs[仕事.id].retried == 1
    assert [type(e) for e in 帳簿.events] == [CheckStopped, Retried]


def test_在りかの指す成果が置き場に無ければ触らない() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Submitted(assignee=働き手), result_at="result://幻")
    帳簿.jobs[仕事.id] = 仕事
    assert run_check(帳簿, 状態の読みの偽物(帳簿), 成果置き場の偽物(), 固定時計()) == ()
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events
