"""作成元の鍵の読みの壊しかた。設計/仕事が回る筋道.md §4——二度作らない（I3）の材料。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from app.ports.origin_reader import OriginReader


def test_返すのは鍵の集まりだけ() -> None:
    hints = get_type_hints(OriginReader.keys)
    assert hints["return"] == frozenset[str]
    assert list(inspect.signature(OriginReader.keys).parameters) == ["self"]
