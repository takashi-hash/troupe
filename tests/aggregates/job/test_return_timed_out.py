"""時間切れを戻すの壊しかた。設計/仕事とは何か.md §6 遷移表・I1。"""

from __future__ import annotations

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import InProgress, Ready
from domain.aggregates.job.return_timed_out import return_timed_out
from domain.events.job.job_timed_out import JobTimedOut
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.clock import Clock
from tests.aggregates.job.conftest import make_job, いま

一号 = Agent(name="一号")


def test_実行中から着手できるへ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = return_timed_out(make_job(InProgress(assignee=一号)), now=いま)
    assert isinstance(仕事.state, Ready)
    assert isinstance(出来事, JobTimedOut)
    assert 出来事.was == 一号 and 出来事.at == いま


def test_起こす者は時計() -> None:
    """時計が起こす——担当ではない。誰の担当だったかは `was` に残る。"""
    _, 出来事 = return_timed_out(make_job(InProgress(assignee=一号)), now=いま)
    assert 出来事.by == Clock()
    assert 出来事.was == 一号


def test_着手できるを渡して戻す行は型で赤() -> None:
    """行けない遷移は型が作らせない——から状態の型が門番。

    下の行は pyright が赤にする（`Job[Ready]` は `Job[InProgress]` に渡せない）。
    実行はしない——赤を見るのは型検査。
    """

    def 書けない行(着手できる: Job[Ready]) -> None:
        return_timed_out(着手できる, now=いま)  # type: ignore[arg-type]  # pyright: reportArgumentType が赤にする

    assert callable(書けない行)  # 呼ばない
