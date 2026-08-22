"""対象期間の壊しかた。設計/仕事とは何か.md §3・§7。

**月なら `2026-08`、週なら `2026-W34` の形だけ。**
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.values.calendar.cycle import Cycle
from domain.values.calendar.period import Period


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    assert Period(text="2026-08") == Period(text="2026-08")
    assert {Period(text="2026-W34"): "第34週"}[Period(text="2026-W34")] == "第34週"


def test_作ったあと書き換えられない() -> None:
    with pytest.raises(ValidationError):
        Period(text="2026-08").text = "来月"  # type: ignore[misc]


def test_月の対象期間が作れて_周期は月と読める() -> None:
    for text in ("2026-01", "2026-08", "2026-12"):
        assert Period(text=text).cycle is Cycle.MONTHLY


def test_週の対象期間が作れて_周期は週と読める() -> None:
    for text in ("2026-W01", "2026-W34", "2026-W53"):
        assert Period(text=text).cycle is Cycle.WEEKLY


def test_言葉の対象期間は作れない() -> None:
    for text in ("来月", "今週", "", "   "):
        with pytest.raises(ValidationError):
            Period(text=text)


def test_形の違う対象期間は作れない() -> None:
    for text in ("2026", "202608", "2026-8", "2026/08", "2026-08-01", "26-08", "2026-w34"):
        with pytest.raises(ValidationError):
            Period(text=text)


def test_月は01から12だけ通す() -> None:
    for text in ("2026-00", "2026-13", "2026-99"):
        with pytest.raises(ValidationError):
            Period(text=text)


def test_週はW01からW53だけ通す() -> None:
    for text in ("2026-W00", "2026-W54", "2026-W99", "2026-W3"):
        with pytest.raises(ValidationError):
            Period(text=text)
