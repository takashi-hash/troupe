"""下書きを配達する（domain）の壊しかた。仕事とは何か §6——状態は変わらない・承認前は刻めない。"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.aggregates.job.deliver_drafts import deliver_drafts
from domain.aggregates.job.life import Cleared, Ready
from domain.events.job.draft_delivered import DraftDelivered
from domain.value_objects.job.approval import Approval
from domain.value_objects.people.clock import Clock
from tests.aggregates.job.conftest import make_job, いま, 座長

承認 = Cleared(approval=Approval(by=座長, at=いま))
のち = datetime(2026, 8, 24, 9, 0, tzinfo=UTC)


def test_承認済みなら同じ状態のまま配達の出来事が残る() -> None:
    job = make_job(承認, result_at="result://1")
    対 = deliver_drafts(job, のち)
    assert 対 is not None
    次, 出来事 = 対
    assert 次.state == job.state  # 状態は変わらない
    assert isinstance(出来事, DraftDelivered)
    assert 出来事.by == Clock() and 出来事.at == のち


def test_承認を経ていない状態には何も刻まない() -> None:
    """承認前の提案が診療録に渡る道を、ここで塞ぐ。"""
    assert deliver_drafts(make_job(Ready(), result_at="result://1"), のち) is None


def test_承認済みで成果なしは型が既に殺している() -> None:
    """op の成果ガードは帯と紐——承認済みの禁止状態（成果なし）はそもそも作れない。"""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        make_job(承認, result_at=None)
