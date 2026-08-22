"""仕事が配られたの壊しかた。設計/仕事が回る筋道.md §5——足して残るものは無い。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_handed_out import JobHandedOut
from domain.values.people.clock import Clock

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_仕事が配られたは誰がといつだけを残す() -> None:
    出来事 = JobHandedOut(at=いま, by=Clock())
    assert set(JobHandedOut.model_fields) == {"at", "by"}
    assert 出来事.by == Clock()


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        JobHandedOut(at=いま, by=Clock(), 中身="x")  # type: ignore[call-arg]
