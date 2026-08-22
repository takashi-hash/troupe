"""時間切れで戻ったの壊しかた。設計/仕事が回る筋道.md §5——時計が起こす。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_timed_out import JobTimedOut
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.clock import Clock

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
番頭 = Agent(name="番頭")


def test_時間切れで戻ったは誰の担当だったかを残す() -> None:
    出来事 = JobTimedOut(at=いま, by=Clock(), was=番頭)
    assert set(JobTimedOut.model_fields) == {"at", "by", "was"}
    assert 出来事.was == 番頭 and 出来事.by == Clock()


def test_外れた担当は素の文字列から作れない() -> None:
    with pytest.raises(ValidationError):
        JobTimedOut(at=いま, by=Clock(), was="番頭")  # type: ignore[arg-type]
