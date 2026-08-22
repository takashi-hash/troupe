"""手放されたの壊しかた。設計/仕事が回る筋道.md §5——離すのは担当。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_released import JobReleased
from domain.values.people.agent import Agent
from domain.values.people.human import Human

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
番頭 = Agent(name="番頭")


def test_手放されたは誰が離したかを残す() -> None:
    出来事 = JobReleased(at=いま, by=番頭, released=番頭)
    assert set(JobReleased.model_fields) == {"at", "by", "released"}
    assert 出来事.released == 番頭


def test_離した担当は人でもよい() -> None:
    座長 = Human(name="座長")
    assert JobReleased(at=いま, by=座長, released=座長).released == 座長


def test_離した担当は素の文字列から作れない() -> None:
    with pytest.raises(ValidationError):
        JobReleased(at=いま, by=番頭, released="番頭")  # type: ignore[arg-type]
