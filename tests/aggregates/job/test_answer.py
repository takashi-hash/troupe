"""答えるの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I7。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.answer import answer
from domain.aggregates.job.job import Job
from domain.aggregates.job.life import AwaitingAnswer, InProgress, Ready
from domain.events.job.question_answered import QuestionAnswered
from domain.value_objects.job.answer import Answer
from domain.value_objects.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま, 座長

一号 = Agent(name="一号")


def _答え待ち() -> Job[AwaitingAnswer]:
    return make_job(AwaitingAnswer(assignee=一号))


def test_答え待ちから着手できるへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = answer(_答え待ち(), Answer(by=座長, body="prod の鍵を使ってください"), now=いま)
    assert isinstance(仕事.state, Ready)
    assert isinstance(出来事, QuestionAnswered)
    assert 出来事.by == 座長 and 出来事.body == "prod の鍵を使ってください" and 出来事.at == いま


def test_答えたら担当が外れている() -> None:
    """戻り先は着手できる——実行中へ戻すと、待つあいだに担当が外れた仕事を誰も拾えない。"""
    仕事, 出来事 = answer(_答え待ち(), Answer(by=座長, body="答えです"), now=いま)
    assert isinstance(仕事.state, Ready)
    assert "assignee" not in type(仕事.state).model_fields  # 担当の欄そのものが無い
    assert 出来事.unassigned == 一号  # 誰の担当が外れたかは出来事に残る


def test_AIは答えを作れない() -> None:
    """I7——`Answer` の `by` が `Human` なので、型でも赤、実行時も値が拒む。"""
    with pytest.raises(ValidationError):
        Answer(by=一号, body="答えです")  # type: ignore[arg-type]  # pyright も赤にする


def test_実行中を渡して答える行は型で赤() -> None:
    """行けない遷移は型が作らせない——から状態の型が門番。

    下の行は pyright が赤にする（`Job[InProgress]` は `Job[AwaitingAnswer]` に渡せない）。
    実行はしない——赤を見るのは型検査。
    """

    def 書けない行(実行中: Job[InProgress]) -> None:
        answer(実行中, Answer(by=座長, body="答えです"), now=いま)  # type: ignore[arg-type]  # pyright: reportArgumentType が赤にする

    assert callable(書けない行)  # 呼ばない
