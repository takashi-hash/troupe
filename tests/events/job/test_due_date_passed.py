"""期日を過ぎたの壊しかた。設計/仕事が回る筋道.md §5——時計が主語。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.due_date_passed import DueDatePassed
from domain.values.people.clock import Clock

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_期日を過ぎたはいつと誰がだけを残す() -> None:
    出来事 = DueDatePassed(at=いま, by=Clock())
    assert set(DueDatePassed.model_fields) == {"at", "by"}
    assert 出来事.at == いま and 出来事.by == Clock()


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        DueDatePassed(at=いま, by=Clock(), 中身="x")  # type: ignore[call-arg]
