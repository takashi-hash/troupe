"""写すものの束の壊しかた。設計/仕事とは何か.md §4。

束そのものの義務は薄い——中身の義務は写される値が各自で守る。
ここで確かめるのは**束が版ではない**こと。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.rule.copied import Copied


def test_束は版の番号を持たない() -> None:
    """番号を持ったら、それは束ではなく版。写しに同一性は無い。"""
    assert "number" not in Copied.model_fields


def test_どれか欠けた束は作れない() -> None:
    with pytest.raises(ValidationError):
        Copied()  # type: ignore[call-arg]


def test_束は日数を持つ() -> None:
    """仕事は持たない日数を、束だけが運ぶ——期日になって消えるまで。"""
    assert "days" in Copied.model_fields
