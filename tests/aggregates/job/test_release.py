"""手放すの壊しかた。設計/仕事とは何か.md §6 遷移表・I1。"""

from __future__ import annotations

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import InProgress, Ready
from domain.aggregates.job.release import release
from domain.events.job.job_released import JobReleased
from domain.values.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま, 座長

一号 = Agent(name="一号")


def test_実行中から着手できるへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = release(make_job(InProgress(assignee=一号)), now=いま)
    assert isinstance(仕事.state, Ready)
    assert isinstance(出来事, JobReleased)
    assert 出来事.released == 一号 and 出来事.by == 一号 and 出来事.at == いま


def test_手放したら担当が外れている() -> None:
    """着手できるに担当の欄そのものが無い——誰でもまた取れる。"""
    仕事, _ = release(make_job(InProgress(assignee=一号)), now=いま)
    assert isinstance(仕事.state, Ready)
    assert "assignee" not in type(仕事.state).model_fields


def test_人の担当でも手放せる_出来事のbyも担当() -> None:
    """担当は人か AI のどちらか——起こす者はいまの担当そのもの。"""
    _, 出来事 = release(make_job(InProgress(assignee=座長)), now=いま)
    assert 出来事.released == 座長 and 出来事.by == 座長


def test_着手できるを渡して手放す行は型で赤() -> None:
    """行けない遷移は型が作らせない——から状態の型が門番。

    下の行は pyright が赤にする（`Job[Ready]` は `Job[InProgress]` に渡せない）。
    実行はしない——赤を見るのは型検査。
    """

    def 書けない行(着手できる: Job[Ready]) -> None:
        release(着手できる, now=いま)  # type: ignore[arg-type]  # pyright: reportArgumentType が赤にする

    assert callable(書けない行)  # 呼ばない
