"""業務ルールの識別子の壊しかた。設計/仕事とは何か.md §3。

**これが業務ルールの同一性。** 名で見分けられなければ、版をどこへ積むか決まらない。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.value_objects.rule.rule_name import RuleName


def test_名で業務ルールを見分ける() -> None:
    assert RuleName(text="月次報告").text == "月次報告"


def test_同じ名なら等しく_同じ辞書の鍵になる() -> None:
    assert RuleName(text="月次報告") == RuleName(text="月次報告")
    assert {RuleName(text="月次報告"): "版1"}[RuleName(text="月次報告")] == "版1"


def test_名が違えば別の業務ルール() -> None:
    assert RuleName(text="月次報告") != RuleName(text="週次点検")
    assert len({RuleName(text="月次報告"): "版1", RuleName(text="週次点検"): "版2"}) == 2


def test_あとから名を書き換えられない() -> None:
    with pytest.raises(ValidationError):
        RuleName(text="月次報告").text = "週次点検"  # type: ignore[misc]


def test_名の空な業務ルールの識別子は作れない() -> None:
    for text in ("", "   ", "\n", "　"):
        with pytest.raises(ValidationError):
            RuleName(text=text)
