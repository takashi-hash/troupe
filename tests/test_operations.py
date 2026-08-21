"""遷移の掟のテスト — 設計/6_型/状態モデル.md §2 の写し。docstring が掟の行。"""

from datetime import datetime, timedelta

import pytest

from domain.job import (
    Checkpoint,
    Budget,
    CannotApprove,
    Confirmed,
    Core,
    FromDefinition,
    Job,
    approve,
)

NOW = datetime(2026, 8, 21, 9, 0)


def job_at_checkpoint(assignee: str) -> Job:
    return Job(
        core=Core(
            job_id="タスク-002",
            origin=FromDefinition(definition_name="週次の検査の見張り", version=3, period="2026-W34"),
            board_id="ボード/運転",
            ready_at=NOW,
            deadline=NOW + timedelta(days=9),
            budget=Budget(calls=50, seconds=3600),
        ),
        state=Checkpoint(
            artifact_ref="成果物/週次の検査の見張り/2026-W34",
            position="座長の承認待ち",
            assignee_id="人/座長" if assignee == "人/座長" else assignee,
        ),
    )


def test_only_assignee_can_approve() -> None:
    """承認待ちは担当した人しか承認できない（I2「止まる」）"""
    job = job_at_checkpoint("人/座長")
    with pytest.raises(CannotApprove):
        approve(job, by="人/事務", at=NOW)


def test_assignee_approves_to_confirmed() -> None:
    """担当した人が承認すると承認済みになり、承認の記録が残る"""
    job = job_at_checkpoint("人/座長")
    after = approve(job, by="人/座長", at=NOW)
    assert isinstance(after.state, Confirmed)
    assert after.state.approval is not None
    assert after.state.approval.approved_by == "人/座長"


def test_cannot_approve_outside_checkpoint() -> None:
    """承認待ちにいないタスクは承認できない"""
    job = job_at_checkpoint("人/座長")
    confirmed = approve(job, by="人/座長", at=NOW)
    with pytest.raises(CannotApprove):
        approve(confirmed, by="人/座長", at=NOW)
