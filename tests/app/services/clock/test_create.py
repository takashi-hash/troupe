"""作る（app）の壊しかた。設計/仕事が回る筋道.md §1「時計が始めるもの」・I3。"""

from __future__ import annotations

from app.services.clock.create import create
from domain.aggregates.job.life import Created
from domain.events.job.job_created import JobCreated
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.rule.criteria import AcceptanceCriteria
from domain.value_objects.rule.source import Source
from tests.app.services.clock.conftest import (
    make_rule,
    予定の読みの偽物,
    作成元の読みの偽物,
    採番の偽物,
    有効版の読みの偽物,
    規則帳簿の偽物,
)
from tests.app.services.conftest import いま, 固定時計, 帳簿の偽物


def _組み立て(**rule_over: object) -> tuple[帳簿の偽物, 規則帳簿の偽物]:
    帳簿 = 帳簿の偽物()
    規則帳簿 = 規則帳簿の偽物()
    規則 = make_rule(**rule_over)
    規則帳簿.rules[規則.name] = 規則
    return 帳簿, 規則帳簿


def test_有効な版といまから_まだ無い仕事を作る() -> None:
    帳簿, 規則帳簿 = _組み立て()
    作られた = create(
        帳簿, 規則帳簿, 有効版の読みの偽物(規則帳簿), 作成元の読みの偽物(帳簿),
        予定の読みの偽物(), 採番の偽物(), 固定時計(),
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
    予定 = 予定の読みの偽物()
    採番 = 採番の偽物()
    assert len(create(帳簿, 規則帳簿, 有効版, 作成元, 予定, 採番, 固定時計())) == 1
    assert create(帳簿, 規則帳簿, 有効版, 作成元, 予定, 採番, 固定時計()) == ()
    assert len(帳簿.jobs) == 1 and len(帳簿.events) == 1


def test_有効な版が無ければ何も作らない() -> None:
    帳簿, 規則帳簿 = _組み立て(active=None, activated_by=None, activated_at=None)
    作られた = create(
        帳簿, 規則帳簿, 有効版の読みの偽物(規則帳簿), 作成元の読みの偽物(帳簿),
        予定の読みの偽物(), 採番の偽物(), 固定時計(),
    )
    assert 作られた == () and not 帳簿.jobs and not 帳簿.events


def _穴あきの版(number: int = 1) -> dict[str, object]:
    """源に `{患者}` の穴・基準にも `{患者}`——展開される版の姿。"""
    base = make_rule().versions[0]
    return {
        "versions": (
            base.model_copy(
                update={
                    "number": number,
                    "source": Source(location="db:chart/{患者}"),
                    "criteria": AcceptanceCriteria(required_terms=("{対象期間}", "{患者}")),
                }
            ),
        ),
        "active": number,
    }


def test_穴あきの版は期間内に予定のある患者ごとに1つ作り_穴は開かれて写る() -> None:
    """筋道 §1 `create`——源と基準の穴は患者記号で、鍵には患者が入る。"""
    帳簿, 規則帳簿 = _組み立て(**_穴あきの版())
    作られた = create(
        帳簿, 規則帳簿, 有効版の読みの偽物(規則帳簿), 作成元の読みの偽物(帳簿),
        予定の読みの偽物((("P-001", "2026-08-18"), ("P-004", "2026-08-19"))),
        採番の偽物(), 固定時計(),
    )
    assert len(作られた) == 2
    期間 = Period.of(いま, Cycle.WEEKLY)
    仕事たち = sorted(帳簿.jobs.values(), key=lambda j: j.source.location)
    assert [j.source.location for j in 仕事たち] == ["db:chart/P-001", "db:chart/P-004"]
    assert 仕事たち[0].criteria.required_terms == (期間.text, "P-001")
    assert 仕事たち[0].origin.key.endswith(f"/{期間.text}/P-001")


def test_穴あきの版で予定が無ければ何も作らない() -> None:
    """下書きの相手が居ない——0件は正しい姿。"""
    帳簿, 規則帳簿 = _組み立て(**_穴あきの版())
    作られた = create(
        帳簿, 規則帳簿, 有効版の読みの偽物(規則帳簿), 作成元の読みの偽物(帳簿),
        予定の読みの偽物(), 採番の偽物(), 固定時計(),
    )
    assert 作られた == () and not 帳簿.jobs


def test_展開も何度回しても同じ_二度目は何も作らない() -> None:
    """I3 は展開後の鍵で守られる——患者ごとの鍵が既にあれば作らない。"""
    帳簿, 規則帳簿 = _組み立て(**_穴あきの版())
    有効版 = 有効版の読みの偽物(規則帳簿)
    作成元 = 作成元の読みの偽物(帳簿)
    予定 = 予定の読みの偽物((("P-001", "2026-08-18"),))
    採番 = 採番の偽物()
    assert len(create(帳簿, 規則帳簿, 有効版, 作成元, 予定, 採番, 固定時計())) == 1
    assert create(帳簿, 規則帳簿, 有効版, 作成元, 予定, 採番, 固定時計()) == ()
    assert len(帳簿.jobs) == 1
