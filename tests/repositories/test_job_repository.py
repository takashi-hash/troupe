"""帳簿の宣言の壊しかた。設計/仕事が回る筋道.md §4・I1。

宣言は Protocol——実装の義務はここで言い切り、実装のテストが同じ検査を通る。
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from domain.events.event import Event
from domain.repositories.job_repository import JobRepository


def test_書き込みの門は姿と出来事の対しか受けない() -> None:
    """I1 — 出来事なしで状態を書く口が無い。"""
    hints = get_type_hints(JobRepository.save)
    assert hints["events"] == tuple[Event, ...]
    params = list(inspect.signature(JobRepository.save).parameters)
    assert params == ["self", "job", "events"]


def test_読みは鍵で1件だけ() -> None:
    params = list(inspect.signature(JobRepository.load).parameters)
    assert params == ["self", "id"]
