"""時計の実装の壊しかた。設計/どう作るか.md §4——「いま」を注ぐ口の中身。"""

from __future__ import annotations

from datetime import timedelta

from adapters.clock import SystemClock
from app.ports.clock_port import ClockPort


def test_UTCでawareな時刻が返る() -> None:
    clock: ClockPort = SystemClock()
    now = clock.now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_時は戻らない() -> None:
    clock = SystemClock()
    first = clock.now()
    second = clock.now()
    assert first <= second
