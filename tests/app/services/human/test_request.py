"""頼む（app）の壊しかた。設計/仕事が回る筋道.md §1・§3・人に見えるもの §3。"""

from __future__ import annotations

from app.services.human.request import request
from domain.aggregates.job.life import Created
from domain.events.job.job_created import JobCreated
from domain.events.job.job_requested import JobRequested
from domain.values.job.request import Request
from domain.values.rule.criteria import AcceptanceCriteria
from tests.aggregates.job.conftest import make_copied, 座長
from tests.app.services.conftest import 固定時計, 帳簿の偽物, 連番の識別子, いま


def _依頼() -> Request:
    return Request(by=座長, at=いま, body="今週の依存も棚卸しして")


def test_振って_作って_出来事2つを対で書く() -> None:
    """頼む＝`JobRequested`＋`JobCreated`——1つの遷移で出来事が2つ、対のまま書かれる。"""
    帳簿 = 帳簿の偽物()
    断り = request(帳簿, 連番の識別子(), 固定時計(), _依頼(), make_copied())
    assert 断り is None
    assert len(帳簿.jobs) == 1
    仕事 = next(iter(帳簿.jobs.values()))
    assert isinstance(仕事.state, Created)
    assert 仕事.origin.key.startswith("request:")  # 作成元は依頼の識別子（I3）
    assert [type(e) for e in 帳簿.events] == [JobRequested, JobCreated]


def test_識別子はIdPortが振る() -> None:
    帳簿 = 帳簿の偽物()
    識別子 = 連番の識別子()
    request(帳簿, 識別子, 固定時計(), _依頼(), make_copied())
    assert 識別子.count == 2  # 仕事の識別子と依頼の識別子——立てた者が振る
    assert next(iter(帳簿.jobs)).text == "ID-0001"


def test_開かれていない差し込みは断りに変わる() -> None:
    """依頼発の基準に差し込みは書けない——義務が拒み、エラーではなく断りが返る。"""
    帳簿 = 帳簿の偽物()
    束 = make_copied(criteria=AcceptanceCriteria(required_terms=("{対象期間}",)))
    断り = request(帳簿, 連番の識別子(), 固定時計(), _依頼(), 束)
    assert 断り is not None
    assert not 帳簿.jobs and not 帳簿.events
