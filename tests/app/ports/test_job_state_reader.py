"""状態の読みの壊しかた。設計/仕事が回る筋道.md §4——一覧と絞り込みは Reader。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from app.ports.job_state_reader import JobStateReader
from domain.value_objects.job.job_id import JobId


def test_返すのは識別子だけ() -> None:
    assert get_type_hints(JobStateReader.ids_in)["return"] == tuple[JobId, ...]


def test_状態で引き_担当でも絞れる() -> None:
    sig = inspect.signature(JobStateReader.ids_in)
    assert list(sig.parameters) == ["self", "state_name", "assignee_name"]
    assert sig.parameters["assignee_name"].default is None
