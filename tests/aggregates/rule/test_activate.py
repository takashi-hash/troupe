"""有効にするの壊しかた。設計/仕事とは何か.md §4・仕事が回る筋道.md §1・I7。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.aggregates.rule.activate import activate
from domain.events.rule.rule_activated import RuleActivated
from domain.values.people.agent import Agent
from tests.aggregates.rule.conftest import make_rule, make_version, いま, 名, 座長


def test_有効になる_出来事が必ず一緒に返る() -> None:
    """返りは（次の姿, 出来事）の対で、片方だけが返せない。"""
    ルール, 出来事 = activate(make_rule(), 1, by=座長, now=いま)
    assert ルール.active == 1
    assert ルール.activated_by == 座長 and ルール.activated_at == いま
    assert isinstance(出来事, RuleActivated)
    assert 出来事.rule_name == 名 and 出来事.version == 1
    assert 出来事.by == 座長 and 出来事.at == いま


def test_版2を有効にすると版1は自動で無効になる() -> None:
    """有効な版の番号は0か1つ——番号の差し替えなので、前の版に手は要らない。"""
    版1が有効 = make_rule(
        versions=(make_version(1), make_version(2)),
        active=1,
        activated_by=座長,
        activated_at=いま,
    )
    ルール, 出来事 = activate(版1が有効, 2, by=座長, now=いま)
    assert ルール.active == 2  # 版1はもう有効ではない
    assert 出来事.version == 2


def test_無い番号は有効にできない() -> None:
    with pytest.raises(ValueError, match="無い版"):
        activate(make_rule(), 9, by=座長, now=いま)


def test_AIは有効にできない() -> None:
    """I7 — この行は型検査も赤にする（`by: Human` に `Agent` を渡している）。
    実行時も `Rule` の欄の型 `activated_by: Human` が拒む——AI が有効にした姿が書けない。
    """
    一号 = Agent(name="一号")
    with pytest.raises(ValidationError):
        activate(make_rule(), 1, by=一号, now=いま)  # type: ignore[arg-type]
