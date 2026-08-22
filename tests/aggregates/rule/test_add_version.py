"""版を積むの壊しかた。設計/仕事が回る筋道.md §1・I2。"""

from __future__ import annotations

import pytest

from domain.aggregates.rule.add_version import add_version
from domain.events.rule.rule_version_added import RuleVersionAdded
from domain.values.rule.rule_name import RuleName
from tests.aggregates.rule.conftest import make_rule, make_version, いま, 名, 座長


def test_無から1版目として業務ルールごと生まれる_出来事が必ず一緒に返る() -> None:
    """返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    ルール, 出来事 = add_version(None, 名, make_version(1), by=座長, now=いま)
    assert ルール.name == 名
    assert tuple(v.number for v in ルール.versions) == (1,)
    assert ルール.active is None
    assert isinstance(出来事, RuleVersionAdded)
    assert 出来事.rule_name == 名 and 出来事.version == 1
    assert 出来事.by == 座長 and 出来事.at == いま


def test_在る業務ルールに次の版が積まれる() -> None:
    ルール, 出来事 = add_version(make_rule(), 名, make_version(2), by=座長, now=いま)
    assert tuple(v.number for v in ルール.versions) == (1, 2)
    assert 出来事.version == 2


def test_1版目は番号1でなければ赤() -> None:
    with pytest.raises(ValueError, match="最後の版"):
        add_version(None, 名, make_version(2), by=座長, now=いま)


def test_版を1つ飛ばして積んだら赤() -> None:
    """I2 — 版は積むだけ。番号は最後の版＋1。"""
    with pytest.raises(ValueError, match="最後の版"):
        add_version(make_rule(), 名, make_version(3), by=座長, now=いま)


def test_積んでも有効な版は動かない() -> None:
    """有効にするのは人の別の判断——積む手は版の列だけを変える。"""
    版1が有効 = make_rule(active=1, activated_by=座長, activated_at=いま)
    ルール, _ = add_version(版1が有効, 名, make_version(2), by=座長, now=いま)
    assert ルール.active == 1 and ルール.activated_by == 座長


def test_別の名の業務ルールには積めない() -> None:
    with pytest.raises(ValueError, match="別の名"):
        add_version(make_rule(), RuleName(text="別の決まり"), make_version(2), by=座長, now=いま)
