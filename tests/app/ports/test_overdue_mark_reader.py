"""期日切れの印の読みの壊しかた。設計/仕事が回る筋道.md §4——二度目を刻まない照合。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from app.ports.overdue_mark_reader import OverdueMarkReader
from domain.value_objects.job.job_id import JobId


def test_返すのは識別子の集まりだけ() -> None:
    hints = get_type_hints(OverdueMarkReader.marked_ids)
    assert hints["return"] == frozenset[JobId]
    assert list(inspect.signature(OverdueMarkReader.marked_ids).parameters) == ["self"]
