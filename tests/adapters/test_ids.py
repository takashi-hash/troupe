"""識別子の実装の壊しかた。設計/どう作るか.md §4——振るたびに違う、空でない。"""

from __future__ import annotations

from adapters.ids import UuidIds
from app.ports.id_port import IdPort


def test_空でない文字が返る() -> None:
    ids: IdPort = UuidIds()
    assert ids.new_id().strip()


def test_2回呼ぶと違う() -> None:
    ids = UuidIds()
    assert ids.new_id() != ids.new_id()
