"""止める（app）の壊しかた。設計/仕事が回る筋道.md §1・人に見えるもの §3。"""

from __future__ import annotations

from app.services.human.deactivate import deactivate
from domain.events.rule.rule_deactivated import RuleDeactivated
from tests.aggregates.rule.conftest import make_rule, 名, 座長
from tests.app.services.conftest import 固定時計, ルール帳簿の偽物


def _有効な帳簿() -> ルール帳簿の偽物:
    帳簿 = ルール帳簿の偽物()
    帳簿.rules[名] = make_rule(
        active=1, activated_by=座長, activated_at=固定時計().now()
    )
    return 帳簿


def test_読んで_止めて_対で書く() -> None:
    帳簿 = _有効な帳簿()
    断り = deactivate(帳簿, 固定時計(), 名.text, by=座長.name)
    assert 断り is None
    assert 帳簿.rules[名].active is None
    assert [type(e) for e in 帳簿.events] == [RuleDeactivated]


def test_止まっているものは断りに変わる() -> None:
    帳簿 = ルール帳簿の偽物()
    帳簿.rules[名] = make_rule()
    断り = deactivate(帳簿, 固定時計(), 名.text, by=座長.name)
    assert 断り is not None and "止まって" in 断り.reason
    assert not 帳簿.events


def test_無い業務ルールは断りに変わる() -> None:
    断り = deactivate(ルール帳簿の偽物(), 固定時計(), "無い決まり", by=座長.name)
    assert 断り is not None and not 断り.reason.startswith("1 validation")
