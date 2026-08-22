"""期日の壊しかた。設計/仕事とは何か.md §3・I12。

**起点より後**。起点も期日も、この値が両方持つ。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from domain.job.due_date import DueDate

起点 = datetime(2026, 8, 22, 9, 0, tzinfo=UTC)


def test_同じ中身なら等しく_同じ辞書の鍵になる() -> None:
    期日 = DueDate(start=起点, at=起点 + timedelta(days=3))
    同じ = DueDate(start=起点, at=起点 + timedelta(days=3))
    assert 期日 == 同じ
    assert {期日: "今日に出す"}[同じ] == "今日に出す"


def test_作ったあと書き換えられない() -> None:
    期日 = DueDate(start=起点, at=起点 + timedelta(days=3))
    with pytest.raises(ValidationError):
        期日.at = 起点 + timedelta(days=30)  # type: ignore[misc]


def test_起点より後の期日は作れる() -> None:
    期日 = DueDate(start=起点, at=起点 + timedelta(days=3))
    assert 期日.start == 起点
    assert 期日.at == datetime(2026, 8, 25, 9, 0, tzinfo=UTC)


def test_起点より前の期日は作れない() -> None:
    with pytest.raises(ValidationError):
        DueDate(start=起点, at=起点 - timedelta(seconds=1))


def test_起点と同じ時刻の期日は作れない() -> None:
    with pytest.raises(ValidationError):
        DueDate(start=起点, at=起点)


def test_起点の時刻と版の日数から組める() -> None:
    assert DueDate.from_start(起点, 3) == DueDate(
        start=起点, at=datetime(2026, 8, 25, 9, 0, tzinfo=UTC)
    )


def test_日数が0なら組めない() -> None:
    with pytest.raises(ValidationError):
        DueDate.from_start(起点, 0)


def test_日数が負なら組めない() -> None:
    with pytest.raises(ValidationError):
        DueDate.from_start(起点, -1)
