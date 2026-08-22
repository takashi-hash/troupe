"""成果が出されたの壊しかた。設計/仕事が回る筋道.md §5——根拠だけが空でありうる。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.result_submitted import ResultSubmitted
from domain.value_objects.people.agent import Agent

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
番頭 = Agent(name="番頭")


def test_成果が出されたは在りかふたつを残す() -> None:
    出来事 = ResultSubmitted(at=いま, by=番頭, result_at="result://1", evidence_at="evidence://1")
    assert set(ResultSubmitted.model_fields) == {"at", "by", "result_at", "evidence_at"}
    assert 出来事.result_at == "result://1" and 出来事.evidence_at == "evidence://1"


def test_引用が取れなければ根拠なしで出せる() -> None:
    出来事 = ResultSubmitted(at=いま, by=番頭, result_at="result://1", evidence_at=None)
    assert 出来事.evidence_at is None


def test_成果の在りかは欠かせない() -> None:
    with pytest.raises(ValidationError):
        ResultSubmitted(at=いま, by=番頭, evidence_at=None)  # type: ignore[call-arg]
