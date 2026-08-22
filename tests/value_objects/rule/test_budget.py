"""使用上限の壊しかた。設計/仕事とは何か.md §3・I14。

**暴走を止める安全弁。** 0や負の使用上限は、ここで殺す。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.value_objects.rule.budget import Budget


def test_回数も秒も1以上なら作れる() -> None:
    上限 = Budget(calls=20, seconds=600)
    assert (上限.calls, 上限.seconds) == (20, 600)


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert Budget(calls=20, seconds=600) == Budget(calls=20, seconds=600)
    assert {Budget(calls=20, seconds=600): "版1"}[Budget(calls=20, seconds=600)] == "版1"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        Budget(calls=20, seconds=600).calls = 99  # type: ignore[misc]


def test_回数が0の使用上限は作れない() -> None:
    with pytest.raises(ValidationError):
        Budget(calls=0, seconds=600)


def test_秒が0の使用上限は作れない() -> None:
    with pytest.raises(ValidationError):
        Budget(calls=20, seconds=0)


def test_負の使用上限は作れない() -> None:
    with pytest.raises(ValidationError):
        Budget(calls=-1, seconds=600)
    with pytest.raises(ValidationError):
        Budget(calls=20, seconds=-1)
