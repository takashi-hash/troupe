"""人の操作 — 画面から来る、人間だけの行為。

判断は人間（公理）。ここを通る操作は必ず出来事に残り、誰がいつ押したかが辿れる。
"""

from __future__ import annotations

from datetime import datetime

from domain.event import Event
from domain.job import CannotApprove, approve
from domain.ports import LedgerPort


def record_approval(ledger: LedgerPort, job_id: str, by: str, now: datetime) -> bool:
    """承認を記録する — 人が押した承認を帳簿に書き込む。担当した人でなければ偽"""
    got = ledger.jobs.get(job_id)
    if got is None:
        return False
    job, rev = got
    try:
        approved = approve(job, by=by, at=now)
    except CannotApprove:
        return False
    return ledger.jobs.put(
        approved,
        rev,
        [Event(kind="CheckpointApproved", at=now, job_id=job_id, payload={"by": by})],
    )
