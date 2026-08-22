"""着手されたの壊しかた。設計/仕事が回る筋道.md §5——取るのは AI。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_started import JobStarted
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.human import Human

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
番頭 = Agent(name="番頭")


def test_着手されたは誰が取ったかを残す() -> None:
    出来事 = JobStarted(at=いま, by=番頭, took=番頭)
    assert set(JobStarted.model_fields) == {"at", "by", "took"}
    assert 出来事.took == 番頭


def test_人は取れない() -> None:
    """取ったかどの型が `Agent`——人が取った形は書けない。"""
    with pytest.raises(ValidationError):
        JobStarted(at=いま, by=番頭, took=Human(name="座長"))  # type: ignore[arg-type]


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        JobStarted(at=いま, by=番頭, took=番頭, 中身="x")  # type: ignore[call-arg]
