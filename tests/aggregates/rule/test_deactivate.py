"""止めるの壊しかた。設計/仕事が回る筋道.md §1・仕事とは何か §4。"""

from __future__ import annotations

import pytest

from domain.aggregates.rule.activate import activate
from domain.aggregates.rule.deactivate import deactivate
from domain.events.rule.rule_deactivated import RuleDeactivated
from tests.aggregates.rule.conftest import make_rule, いま, 座長


def _有効な業務ルール():  # type: ignore[no-untyped-def]
    rule, _ = activate(make_rule(), 1, by=座長, now=いま)
    return rule


def test_止めると有効な版が空に戻る() -> None:
    rule, 出来事 = deactivate(_有効な業務ルール(), by=座長, now=いま)
    assert rule.active is None and rule.activated_by is None and rule.activated_at is None
    assert isinstance(出来事, RuleDeactivated) and 出来事.version == 1


def test_版の列はそのまま() -> None:
    """止まっても歴史は消えない——版は積むだけ（I2）。"""
    元 = _有効な業務ルール()
    rule, _ = deactivate(元, by=座長, now=いま)
    assert rule.versions == 元.versions


def test_止まっているものは止められない() -> None:
    with pytest.raises(ValueError, match="もう止まって"):
        deactivate(make_rule(), by=座長, now=いま)


def test_また有効にできる() -> None:
    """止める→有効にするは行き来できる——決めるのはいつも人。"""
    rule, _ = deactivate(_有効な業務ルール(), by=座長, now=いま)
    再開, _ = activate(rule, 1, by=座長, now=いま)
    assert 再開.active == 1
