"""答える（app）の壊しかた。設計/仕事が回る筋道.md §1・§4・人に見えるもの §3。"""

from __future__ import annotations

from app.services.human.answer import answer
from domain.aggregates.job.life import AwaitingAnswer, Ready
from domain.events.job.question_answered import QuestionAnswered
from domain.value_objects.job.job_id import JobId
from domain.value_objects.people.agent import Agent
from tests.aggregates.job.conftest import make_job, 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物

一号 = Agent(name="一号")


def test_読んで_着手できるへ_対で書く() -> None:
    帳簿 = 帳簿の偽物()
    仕事 = make_job(AwaitingAnswer(assignee=一号))
    帳簿.jobs[仕事.id] = 仕事
    断り = answer(帳簿, 固定時計(), 仕事.id.text, by=座長.name, body="prod の鍵を使ってください")
    assert 断り is None
    assert isinstance(帳簿.jobs[仕事.id].state, Ready)
    (出来事,) = 帳簿.events
    assert isinstance(出来事, QuestionAnswered)
    assert 出来事.body == "prod の鍵を使ってください"  # 回答の本文は出来事が完載する——正本


def test_答え待ちでなければ断りに変わる_出来事も刻まれない() -> None:
    """操作の失敗はエラーではない——状態は変わらず、帳簿にも何も残らない。"""
    帳簿 = 帳簿の偽物()
    仕事 = make_job(Ready())
    帳簿.jobs[仕事.id] = 仕事
    断り = answer(帳簿, 固定時計(), 仕事.id.text, by=座長.name, body="答えです")
    assert 断り is not None and "答えを待っていません" in 断り.reason
    assert not 帳簿.events
    assert 帳簿.jobs[仕事.id] == 仕事


def test_無い仕事は断りに変わる() -> None:
    断り = answer(帳簿の偽物(), 固定時計(), "J-9999", by=座長.name, body="答えです")
    assert 断り is not None
