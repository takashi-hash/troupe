"""終わったの壊しかた。設計/仕事が回る筋道.md §5・I5——どちらか一方だけ。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from domain.events.job.job_finished import JobFinished
from domain.value_objects.people.clock import Clock

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
確かめ期日 = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)


def test_根拠ありで終われる() -> None:
    出来事 = JobFinished(at=いま, by=Clock(), evidence_at="evidence://1", recheck_at=None)
    assert set(JobFinished.model_fields) == {"at", "by", "evidence_at", "recheck_at"}
    assert 出来事.evidence_at == "evidence://1" and 出来事.recheck_at is None


def test_根拠なしなら確かめ期日つきで終われる() -> None:
    出来事 = JobFinished(at=いま, by=Clock(), evidence_at=None, recheck_at=確かめ期日)
    assert 出来事.evidence_at is None and 出来事.recheck_at == 確かめ期日


def test_両方持つ形も両方欠く形も書けない() -> None:
    """I5——終わったと言うには、根拠か確かめ期日のどちらか一方だけ。"""
    with pytest.raises(ValidationError, match="どちらか一方"):
        JobFinished(at=いま, by=Clock(), evidence_at="evidence://1", recheck_at=確かめ期日)
    with pytest.raises(ValidationError, match="どちらか一方"):
        JobFinished(at=いま, by=Clock(), evidence_at=None, recheck_at=None)
