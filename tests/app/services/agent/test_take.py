"""着手する（app）の壊しかた。設計/仕事が回る筋道.md §1「AI が始めるもの」。"""

from __future__ import annotations

from app.services.agent.take import take
from app.services.refusal import Refusal
from domain.aggregates.job.life import InProgress, Ready
from domain.events.job.job_started import JobStarted
from tests.aggregates.job.conftest import make_job
from tests.app.services.conftest import 固定時計, 帳簿の偽物
from tests.app.services.agent.conftest import 働き手, 状態読みの偽物


def test_着手できるを1件取り実行中へ() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Ready())
    帳簿.jobs[仕事.id] = 仕事
    取れた = take(帳簿, 状態読みの偽物({"Ready": (仕事.id,)}), 固定時計(), by=働き手)
    assert 取れた == 仕事.id
    後 = 帳簿.jobs[仕事.id]
    assert isinstance(後.state, InProgress) and 後.state.assignee == 働き手
    assert [type(e) for e in 帳簿.events] == [JobStarted]


def test_着手できるが無ければ断りに変わる() -> None:
    帳簿 = 帳簿の偽物()
    取れた = take(帳簿, 状態読みの偽物(), 固定時計(), by=働き手)
    assert isinstance(取れた, Refusal) and not 帳簿.events


def test_読みと帳簿がずれていたら断りに変わる() -> None:
    """操作の失敗はエラーではない——状態は変わらず、理由だけが返る。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(InProgress(assignee=働き手))  # 読みは着手できると言ったが、もう取られている
    帳簿.jobs[仕事.id] = 仕事
    取れた = take(帳簿, 状態読みの偽物({"Ready": (仕事.id,)}), 固定時計(), by=働き手)
    assert isinstance(取れた, Refusal)
    assert 帳簿.jobs[仕事.id] == 仕事 and not 帳簿.events
