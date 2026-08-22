"""着手するの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I13。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import InProgress, Ready
from domain.aggregates.job.start import start
from domain.events.job.job_started import JobStarted
from domain.values.people.agent import Agent
from tests.aggregates.job.conftest import make_job, いま, 座長

一号 = Agent(name="一号")


def test_着手できるから実行中へ_出来事が必ず一緒に返る() -> None:
    """I1 が型になる——返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    仕事, 出来事 = start(make_job(Ready()), by=一号, now=いま)
    assert isinstance(仕事.state, InProgress)
    assert 仕事.state.assignee == 一号
    assert isinstance(出来事, JobStarted)
    assert 出来事.took == 一号 and 出来事.by == 一号 and 出来事.at == いま


def test_取った_AI_がここから担当になる() -> None:
    """取る前は担当ではない（I13 の「取るだけは別」）——取ったあとに担当になる。"""
    元 = make_job(Ready())
    仕事, _ = start(元, by=一号, now=いま)
    assert 仕事.state.assignee == 一号
    assert 仕事.id == 元.id and 仕事.origin == 元.origin


def test_実行中を渡して着手する行は型で赤() -> None:
    """行けない遷移は型が作らせない——から状態の型が門番。

    下の行は pyright が赤にする（`Job[InProgress]` は `Job[Ready]` に渡せない）。
    実行はしない——赤を見るのは型検査。
    """

    def 書けない行(実行中: Job[InProgress]) -> None:
        start(実行中, by=一号, now=いま)  # type: ignore[arg-type]  # pyright: reportArgumentType が赤にする

    assert callable(書けない行)  # 呼ばない


def test_人は取れない() -> None:
    """取るのは取ろうとする AI だけ——`by` の型が `Agent` なので型でも赤、実行時も出来事が拒む。"""
    with pytest.raises(ValidationError):
        start(make_job(Ready()), by=座長, now=いま)  # type: ignore[arg-type]  # pyright も赤にする
