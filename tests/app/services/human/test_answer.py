"""答える（app）の壊しかた。設計/仕事が回る筋道.md §1・§4・人に見えるもの §3。"""

from __future__ import annotations

from app.services.human.answer import answer
from domain.aggregates.job.life import AwaitingAnswer, Ready
from domain.value_objects.job.answer import Answer
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.question import Question
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.owner import Owner
from tests.aggregates.job.conftest import make_job, 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物, 質問置き場の偽物

一号 = Agent(name="一号")


def test_読んで_回答を積んで_着手できるへ_対で書く() -> None:
    帳簿 = 帳簿の偽物()
    置き場 = 質問置き場の偽物()
    質問 = Question(body="どの鍵を使いますか", to=Owner(person=座長))
    在りか = 置き場.put_question(質問)
    仕事 = make_job(AwaitingAnswer(assignee=一号, question_at=在りか))
    帳簿.jobs[仕事.id] = 仕事
    断り = answer(帳簿, 置き場, 固定時計(), 仕事.id.text, by=座長.name, body="prod の鍵を使ってください")
    assert 断り is None
    assert isinstance(帳簿.jobs[仕事.id].state, Ready)
    assert 置き場.get(在りか) == (質問, Answer(by=座長, body="prod の鍵を使ってください"))  # 回答は質問の在りかへ紐づく
    assert len(帳簿.events) == 1


def test_答え待ちでなければ断りに変わる_回答も積まれない() -> None:
    """操作の失敗はエラーではない——状態は変わらず、置き場にも何も残らない。"""
    帳簿 = 帳簿の偽物()
    置き場 = 質問置き場の偽物()
    仕事 = make_job(Ready())
    帳簿.jobs[仕事.id] = 仕事
    断り = answer(帳簿, 置き場, 固定時計(), 仕事.id.text, by=座長.name, body="答えです")
    assert 断り is not None and "答えを待っていません" in 断り.reason
    assert not 置き場.answers and not 帳簿.events
    assert 帳簿.jobs[仕事.id] == 仕事


def test_無い仕事は断りに変わる() -> None:
    断り = answer(
        帳簿の偽物(), 質問置き場の偽物(), 固定時計(), "J-9999", by=座長.name, body="答えです"
    )
    assert 断り is not None
