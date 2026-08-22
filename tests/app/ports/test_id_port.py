"""識別子の口の壊しかた。設計/仕事が回る筋道.md §4——採番はファクトリの外。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from app.ports.id_port import IdPort


def test_振るのは新しい識別子だけ() -> None:
    assert get_type_hints(IdPort.new_id)["return"] is str
    assert list(inspect.signature(IdPort.new_id).parameters) == ["self"]
