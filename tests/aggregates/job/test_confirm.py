"""確かめるの壊しかた。設計/仕事とは何か.md §6 遷移表・I1・I5。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.job.confirm import confirm
from domain.aggregates.job.job import Job
from domain.aggregates.job.life import Cleared, Finished, FinishedPendingRecheck
from domain.events.job.job_finished import JobFinished
from domain.events.job.recheck_date_pushed import RecheckDatePushed
from domain.values.calendar.cycle import Cycle
from domain.values.job.approval import Approval
from domain.values.job.due_date import DueDate
from domain.values.job.recheck_date import RecheckDate
from domain.values.people.clock import Clock
from tests.aggregates.job.conftest import make_job, いま, 座長

承認 = Approval(by=座長, at=いま)
期日 = DueDate.from_start(いま, 3)


def _cleared(**over: object) -> Job[Cleared]:
    return make_job(Cleared(approval=承認), result_at="result://1", **over)


def _pending() -> Job[FinishedPendingRecheck]:
    return make_job(
        FinishedPendingRecheck(approval=承認, recheck=RecheckDate.first(期日, Cycle.WEEKLY)),
        result_at="result://1",
    )


def test_承認済みで根拠があれば終わった() -> None:
    仕事, 出来事 = confirm(_cleared(evidence_at="evidence://1"), None, いま)
    assert isinstance(仕事.state, Finished) and 仕事.evidence_at == "evidence://1"
    assert isinstance(出来事, JobFinished)
    assert 出来事.evidence_at == "evidence://1" and 出来事.recheck_at is None
    assert 出来事.by == Clock() and 出来事.at == いま


def test_承認済みで引用が読めたら持たせて終わった() -> None:
    仕事, 出来事 = confirm(_cleared(), "evidence://fetched", いま)
    assert isinstance(仕事.state, Finished) and 仕事.evidence_at == "evidence://fetched"
    assert isinstance(出来事, JobFinished) and 出来事.evidence_at == "evidence://fetched"


def test_承認済みでどちらも無ければ確かめ待ちへ() -> None:
    """確かめ期日は期日＋写した周期——AI が決めるのではない。"""
    仕事, 出来事 = confirm(_cleared(), None, いま)
    assert isinstance(仕事.state, FinishedPendingRecheck)
    assert 仕事.state.recheck == RecheckDate.first(期日, Cycle.WEEKLY)
    assert 仕事.evidence_at is None
    assert isinstance(出来事, JobFinished)
    assert 出来事.evidence_at is None and 出来事.recheck_at == 仕事.state.recheck.at


def test_確かめ待ちで引用が取れたら終わった() -> None:
    仕事, 出来事 = confirm(_pending(), "evidence://2", いま)
    assert isinstance(仕事.state, Finished) and 仕事.evidence_at == "evidence://2"
    assert isinstance(出来事, JobFinished)
    assert 出来事.evidence_at == "evidence://2" and 出来事.recheck_at is None


def test_確かめ待ちから送ると確かめ期日が進む() -> None:
    """送って進まない値は型が作らせない——基準が前の確かめ期日に移る。"""
    元 = _pending()
    前 = 元.state.recheck
    仕事, 出来事 = confirm(元, None, いま)
    assert isinstance(仕事.state, FinishedPendingRecheck)
    assert 仕事.state.recheck.at > 前.at and 仕事.state.recheck.after == 前.at
    assert isinstance(出来事, RecheckDatePushed) and 出来事.recheck_at == 仕事.state.recheck.at
    assert 出来事.by == Clock() and 出来事.at == いま


def test_確かめ待ちのまま根拠を持てない() -> None:
    """Job の義務——終わった（確かめ待ち）は根拠の在りかを持ってはいけない。"""
    with pytest.raises(ValidationError, match="根拠の在りか"):
        make_job(
            FinishedPendingRecheck(approval=承認, recheck=RecheckDate.first(期日, Cycle.WEEKLY)),
            result_at="result://1",
            evidence_at="evidence://1",
        )


def test_確かめた仕事は持ちものを引き継ぐ() -> None:
    元 = _cleared(evidence_at="evidence://1")
    仕事, _ = confirm(元, None, いま)
    assert 仕事.id == 元.id and 仕事.origin == 元.origin
    assert 仕事.result_at == "result://1"
