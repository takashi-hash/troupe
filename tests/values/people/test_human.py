"""人の壊しかた。設計/仕事とは何か.md §3。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.values.people.human import Human


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert Human(name="座長") == Human(name="座長")
    assert {Human(name="座長"): "受け持ち"}[Human(name="座長")] == "受け持ち"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        Human(name="座長").name = "別人"  # type: ignore[misc]


def test_知らない欄では作れない() -> None:
    with pytest.raises(ValidationError):
        Human(name="座長", 役職="座長")  # type: ignore[call-arg]


def test_名の空な人は作れない() -> None:
    for text in ("", "   "):
        with pytest.raises(ValidationError):
            Human(name=text)
