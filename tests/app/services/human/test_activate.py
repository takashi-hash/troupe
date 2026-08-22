"""有効にする（app）の壊しかた。設計/仕事が回る筋道.md §1・人に見えるもの §3。"""

from __future__ import annotations

from app.services.human.activate import activate
from domain.events.rule.rule_activated import RuleActivated
from domain.value_objects.rule.rule_name import RuleName
from tests.aggregates.rule.conftest import make_rule, 名, 座長
from tests.app.services.conftest import 固定時計, ルール帳簿の偽物


def test_読んで_有効にして_対で書く() -> None:
    帳簿 = ルール帳簿の偽物()
    帳簿.rules[名] = make_rule()
    断り = activate(帳簿, 固定時計(), 名.text, 1, by=座長.name)
    assert 断り is None
    ルール = 帳簿.rules[名]
    assert ルール.active == 1 and ルール.activated_by == 座長
    assert [type(e) for e in 帳簿.events] == [RuleActivated]


def test_無い版は断りに変わる() -> None:
    """操作の失敗はエラーではない——版の列は変わらず、理由だけが返る。"""
    帳簿 = ルール帳簿の偽物()
    帳簿.rules[名] = make_rule()
    断り = activate(帳簿, 固定時計(), 名.text, 2, by=座長.name)
    assert 断り is not None and "無い版" in 断り.reason
    assert 帳簿.rules[名].active is None and not 帳簿.events


def test_無い業務ルールは断りに変わる() -> None:
    断り = activate(ルール帳簿の偽物(), 固定時計(), "無い決まり", 1, by=座長.name)
    assert 断り is not None
