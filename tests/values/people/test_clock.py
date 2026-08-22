"""時計の壊しかた。設計/仕事が回る筋道.md §1。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.values.people.clock import Clock


def test_時計に中身は無く_どれも等しい() -> None:
    assert Clock() == Clock()


def test_時計に名は付けられない() -> None:
    """時計は1つ。名で区別しない。"""
    with pytest.raises(ValidationError):
        Clock(name="毎朝9時")  # type: ignore[call-arg]
