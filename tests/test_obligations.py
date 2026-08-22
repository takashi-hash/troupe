"""全部に共通の義務の壊しかた。設計/仕事とは何か.md §3「全部に共通の義務」。

各値のテストは自分に特有の義務を見る。**共通の義務そのもの**はここで1度だけ見る。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.obligations import Value, not_blank


class 例(Value):
    text: str


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert 例(text="a") == 例(text="a")
    assert hash(例(text="a")) == hash(例(text="a"))
    assert {例(text="a"): 1}[例(text="a")] == 1


def test_違う型なら中身が同じでも辞書で衝突しない() -> None:
    class 別(Value):
        text: str

    assert hash(例(text="a")) != hash(別(text="a"))


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        例(text="a").text = "b"  # type: ignore[misc]


def test_知らない欄では作れない() -> None:
    with pytest.raises(ValidationError):
        例(text="a", 余り="x")  # type: ignore[call-arg]


def test_空でないの判定は空白だけも空と見る() -> None:
    assert not_blank(" a ", "何か") == " a "
    for text in ("", "   ", "\n"):
        with pytest.raises(ValueError):
            not_blank(text, "何か")
