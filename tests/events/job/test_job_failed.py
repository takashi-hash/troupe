"""失敗したの壊しかた。設計/仕事が回る筋道.md §5。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_failed import JobFailed
from domain.values.people.agent import Agent

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_落ちた中身が残る() -> None:
    出来事 = JobFailed(at=いま, by=Agent(name="出納係"), fallen="源が読めない")
    assert set(JobFailed.model_fields) == {"at", "by", "fallen"}
    assert 出来事.fallen == "源が読めない"


def test_落ちた中身が空なら作れない() -> None:
    with pytest.raises(ValidationError, match="落ちた中身"):
        JobFailed(at=いま, by=Agent(name="出納係"), fallen=" ")
