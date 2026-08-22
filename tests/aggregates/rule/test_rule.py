"""業務ルールの集約ルートの壊しかた。設計/仕事とは何か.md §4「業務ルールが持つもの」・I2・I7。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.aggregates.rule.conftest import make_rule, make_version, いま, 座長


def test_版の列の空な業務ルールは作れない() -> None:
    with pytest.raises(ValidationError):
        make_rule(versions=())


def test_版を消した姿が作れない() -> None:
    """I2 — 版は積むだけ。版1を消すと連番が崩れ、姿そのものが書けない。"""
    with pytest.raises(ValidationError):
        make_rule(versions=(make_version(2),))


def test_版を飛ばした姿が作れない() -> None:
    with pytest.raises(ValidationError):
        make_rule(versions=(make_version(1), make_version(3)))


def test_有効な版の番号は在る版の番号だけ() -> None:
    with pytest.raises(ValidationError):
        make_rule(active=9, activated_by=座長, activated_at=いま)


def test_有効なのに人か時刻の欠けた姿が作れない() -> None:
    """有効なら3つ揃い、無効なら3つ空——片方だけの姿が書けない。"""
    with pytest.raises(ValidationError):
        make_rule(active=1)
    with pytest.raises(ValidationError):
        make_rule(activated_by=座長)
    with pytest.raises(ValidationError):
        make_rule(activated_at=いま)


def test_正しい業務ルールは作れる() -> None:
    ルール = make_rule()
    assert tuple(v.number for v in ルール.versions) == (1,)
    assert ルール.active is None and ルール.activated_by is None
    有効 = make_rule(active=1, activated_by=座長, activated_at=いま)
    assert 有効.active == 1
