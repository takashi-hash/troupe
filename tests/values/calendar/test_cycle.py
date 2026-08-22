"""周期の壊しかた。設計/仕事とは何か.md §3。

**月か週のどちらか。3つ目は無い。**
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from domain.values.calendar.cycle import Cycle


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert Cycle("monthly") == Cycle.MONTHLY
    assert {Cycle("weekly"): "毎週"}[Cycle.WEEKLY] == "毎週"


def test_月と週の2つだけ() -> None:
    assert set(Cycle) == {Cycle.MONTHLY, Cycle.WEEKLY}


def test_3つ目の周期は作れない() -> None:
    for text in ("daily", "yearly", "月", ""):
        with pytest.raises(ValueError):
            Cycle(text)


def test_月の幅は31日() -> None:
    assert Cycle.MONTHLY.span == timedelta(days=31)


def test_週の幅は7日() -> None:
    assert Cycle.WEEKLY.span == timedelta(days=7)
