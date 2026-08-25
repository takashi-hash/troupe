"""尋ねるの壊しかた。設計/仕事とは何か.md §6 遷移表・§7「禁止状態」・I1。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.ask import ask
from domain.aggregates.job.job import Job
from domain.aggregates.job.life import AwaitingAnswer, InProgress, Ready
from domain.events.job.question_asked import QuestionAsked
from domain.value_objects.job.question import Question
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner
from tests.aggregates.job.conftest import make_job, いま, 座長

一号 = Agent(name="一号")


def _質問() -> Question:
    return Question(body="源の鍵はどちらを使いますか", to=Owner(person=座長))


def test_実行中から答え待ちへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = ask(make_job(InProgress(assignee=一号)), _質問(), now=いま)
    assert isinstance(仕事.state, AwaitingAnswer)
    assert 仕事.state.assignee == 一号
    assert isinstance(出来事, QuestionAsked)
    assert 出来事.body == _質問().body and 出来事.by == 一号 and 出来事.at == いま


def test_相手が仕事の受け持ちの人でなければ尋ねられない() -> None:
    """相手は仕事の受け持ちの人——AI が選ばない。"""
    よその人 = Question(body="源の鍵はどちらを使いますか", to=Owner(person=Human(name="よその人")))
    with pytest.raises(ValueError, match="受け持ちの人"):
        ask(make_job(InProgress(assignee=一号)), よその人, now=いま)


def test_空の質問では尋ねられない() -> None:
    """質問の無い答え待ちが書けない——尋ねるは空でない質問（値）を必ず受ける。"""
    with pytest.raises(ValidationError):
        Question(body="  ", to=Owner(person=座長))


def test_着手できるを渡して尋ねる行は型で赤() -> None:
    """行けない遷移は型が作らせない——から状態の型が門番。

    下の行は pyright が赤にする（`Job[Ready]` は `Job[InProgress]` に渡せない）。
    実行はしない——赤を見るのは型検査。
    """

    def 書けない行(着手できる: Job[Ready]) -> None:
        ask(着手できる, _質問(), now=いま)  # type: ignore[arg-type]  # pyright: reportArgumentType が赤にする

    assert callable(書けない行)  # 呼ばない
