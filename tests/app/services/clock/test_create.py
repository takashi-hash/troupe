"""作る（app）の壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」・I3。"""

from __future__ import annotations

from app.services.clock.create import create
from domain.aggregates.job.life import Created
from domain.events.job.job_created import JobCreated
from domain.values.calendar.cycle import Cycle
from domain.values.calendar.period import Period
from tests.app.services.clock.conftest import (
    make_rule,
    作成元の読みの偽物,
    採番の偽物,
    有効版の読みの偽物,
    規則帳簿の偽物,
)
from tests.app.services.conftest import いま, 固定時計, 帳簿の偽物


def _組み立て() -> tuple[帳簿の偽物, 規則帳簿の偽物]:
    帳簿 = 帳簿の偽物()
    規則帳簿 = 規則帳簿の偽物()
    規則 = make_rule()
    規則帳簿.rules[規則.name] = 規則
    return 帳簿, 規則帳簿


def test_有効な版といまから_まだ無い仕事を作る() -> None:
    帳簿, 規則帳簿 = _組み立て()
    作られた = create(
        帳簿, 規則帳簿, 有効版の読みの偽物(規則帳簿), 作成元の読みの偽物(帳簿), 採番の偽物(), 固定時計()
    )
    assert len(作られた) == 1
    仕事 = 帳簿.jobs[作られた[0]]
    assert isinstance(仕事.state, Created)
    期間 = Period.of(いま, Cycle.WEEKLY)
    assert 仕事.period == 期間
    assert 仕事.criteria.required_terms == (期間.text,)  # {対象期間} は写すときに開かれ済み
    assert len(帳簿.events) == 1 and isinstance(帳簿.events[0], JobCreated)


def test_何度回しても同じ_二度目は何も作らない() -> None:
    """作成元が一意（I3）——同じ帳簿に2回回して、2度目は何もしない。"""
    帳簿, 規則帳簿 = _組み立て()
    有効版 = 有効版の読みの偽物(規則帳簿)
    作成元 = 作成元の読みの偽物(帳簿)
    採番 = 採番の偽物()
    assert len(create(帳簿, 規則帳簿, 有効版, 作成元, 採番, 固定時計())) == 1
    assert create(帳簿, 規則帳簿, 有効版, 作成元, 採番, 固定時計()) == ()
    assert len(帳簿.jobs) == 1 and len(帳簿.events) == 1


def test_有効な版が無ければ何も作らない() -> None:
    帳簿 = 帳簿の偽物()
    規則帳簿 = 規則帳簿の偽物()
    規則 = make_rule(active=None, activated_by=None, activated_at=None)
    規則帳簿.rules[規則.name] = 規則
    作られた = create(
        帳簿, 規則帳簿, 有効版の読みの偽物(規則帳簿), 作成元の読みの偽物(帳簿), 採番の偽物(), 固定時計()
    )
    assert 作られた == () and not 帳簿.jobs and not 帳簿.events
