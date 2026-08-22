"""検査を回すの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I6。"""

from __future__ import annotations

import pytest

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import AwaitingApproval, Failed, Ready, Submitted
from domain.aggregates.job.run_check import run_check
from domain.events.job.check_passed import CheckPassed
from domain.events.job.check_stopped import CheckStopped
from domain.events.job.job_failed import JobFailed
from domain.events.job.retried import Retried
from domain.values.job.origin import Origin
from domain.values.people.agent import Agent
from domain.values.people.clock import Clock
from domain.values.people.owner import Owner
from domain.values.rule.criteria import AcceptanceCriteria
from tests.aggregates.job.conftest import make_job, いま, 座長

一号 = Agent(name="一号")
通る成果 = "2026-W34 の依存一覧。更新が3件。"
止まる成果 = "先週の一覧です。更新が3件。"


def _submitted(**over: object) -> Job[Submitted]:
    return make_job(Submitted(assignee=一号), result_at="result://1", **over)


def test_通る成果は承認待ちへ_担当が受け持ちの人に移る() -> None:
    """I6 の入り口——承認待ちの担当の型は Owner。"""
    結果 = run_check(_submitted(), 通る成果, now=いま)
    assert len(結果) == 2
    仕事, 出来事 = 結果
    assert isinstance(仕事.state, AwaitingApproval)
    assert 仕事.state.assignee == Owner(person=座長) == 仕事.owner
    assert isinstance(出来事, CheckPassed)
    assert 出来事.moved_to == 仕事.owner and 出来事.by == Clock() and 出来事.at == いま


def test_止まる成果でやり直せるなら着手できるへ_回数が増える() -> None:
    結果 = run_check(_submitted(), 止まる成果, now=いま)
    assert len(結果) == 3
    仕事, 止まり, 続き = 結果
    assert isinstance(仕事.state, Ready) and 仕事.retried == 1
    assert isinstance(止まり, CheckStopped) and "2026-W34" in 止まり.reason
    assert isinstance(続き, Retried) and 続き.times == 1
    assert 止まり.by == Clock() and 続き.by == Clock()


def test_尽きる境界_上限の一歩手前なら着手できる() -> None:
    """retried = max_retries - 1 はまだやり直せる。"""
    結果 = run_check(_submitted(retried=19), 止まる成果, now=いま)
    assert len(結果) == 3
    仕事, _, 続き = 結果
    assert isinstance(仕事.state, Ready) and 仕事.retried == 20
    assert isinstance(続き, Retried) and 続き.times == 20


def test_尽きる境界_上限に達していたら失敗した() -> None:
    """retried = max_retries は尽きた。落ちた中身は止めた理由そのもの。"""
    結果 = run_check(_submitted(retried=20), 止まる成果, now=いま)
    assert len(結果) == 3
    仕事, 止まり, 続き = 結果
    assert isinstance(仕事.state, Failed)
    assert isinstance(止まり, CheckStopped) and 仕事.state.fallen == 止まり.reason
    assert isinstance(続き, JobFailed) and 続き.fallen == 止まり.reason
    assert "assignee" not in type(仕事.state).model_fields  # 失敗したは担当を持てない


def test_同じ成果なら何度回しても同じ行き先() -> None:
    """時計が始めるものは何度回しても同じ結果——文字の照合だけ。"""
    assert len(run_check(_submitted(), 通る成果, now=いま)) == len(
        run_check(_submitted(), 通る成果, now=いま)
    )
    assert len(run_check(_submitted(), 止まる成果, now=いま)) == 3


def test_開かれていない差し込みは検査に届く前に死ぬ() -> None:
    """依頼発の基準に差し込みは書けない——開く相手が居ない。仕事に写る時点で赤。"""
    with pytest.raises(ValueError, match="開かれていない"):
        _submitted(
            origin=Origin.from_request("R-0001"),
            born_of=None,
            born_version=None,
            period=None,
            criteria=AcceptanceCriteria(required_terms=("{対象期間}",)),
        )
