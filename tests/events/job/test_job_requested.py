"""仕事が頼まれたの壊しかた。設計/仕事が回る筋道.md §5——頼めるのは人だけ。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_requested import JobRequested
from domain.value_objects.people.agent import Agent
from domain.value_objects.people.human import Human

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
座長 = Human(name="座長")


def test_仕事が頼まれたは誰がと何をを残す() -> None:
    出来事 = JobRequested(at=いま, by=座長, body="依存の棚卸しをやって")
    assert set(JobRequested.model_fields) == {"at", "by", "body"}
    assert 出来事.by == 座長 and 出来事.body == "依存の棚卸しをやって"


def test_AIは頼めない() -> None:
    """頼んだ人の型が `Human`——AI が頼んだ形は書けない。"""
    with pytest.raises(ValidationError):
        JobRequested(
            at=いま, by=Agent(name="番頭"), body="x"  # type: ignore[arg-type]
        )


def test_足して残す欄を勝手に増やせない() -> None:
    with pytest.raises(ValidationError):
        JobRequested(at=いま, by=座長, body="x", 中身="x")  # type: ignore[call-arg]
