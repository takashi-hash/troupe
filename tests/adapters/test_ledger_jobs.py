"""仕事の帳簿（SQLite）の壊しかた。I1・I3・楽観ロック・再構成。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from adapters.ledger.db import open_ledger
from adapters.ledger.jobs import SqliteJobs
from domain.aggregates.job.approve import approve
from domain.aggregates.job.life import AwaitingApproval, Ready
from domain.events.job.job_handed_out import JobHandedOut
from domain.value_objects.people.clock import Clock
from domain.value_objects.people.owner import Owner
from tests.aggregates.job.conftest import make_job, 座長

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def _帳簿(tmp_path):  # type: ignore[no-untyped-def]
    return SqliteJobs(open_ledger(tmp_path / "ichiza.db"))


def test_積んで読み直すと同じ姿が返る(tmp_path) -> None:  # type: ignore[no-untyped-def]
    帳簿 = _帳簿(tmp_path)
    仕事 = make_job(Ready())
    帳簿.save(仕事, (JobHandedOut(at=いま, by=Clock()),))
    assert 帳簿.load(仕事.id) == 仕事


def test_出来事なしでは書けない(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """I1 — 書き込みの門。"""
    with pytest.raises(ValueError, match="I1"):
        _帳簿(tmp_path).save(make_job(Ready()), ())


def test_同じ作成元の仕事は二度書けない(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """I3 — 帳簿の一意の鍵。"""
    帳簿 = _帳簿(tmp_path)
    帳簿.save(make_job(Ready()), (JobHandedOut(at=いま, by=Clock()),))
    from domain.value_objects.job.job_id import JobId

    同じ作成元 = make_job(Ready(), id=JobId(text="J-0002"))
    with pytest.raises(ValueError, match="I3"):
        帳簿.save(同じ作成元, (JobHandedOut(at=いま, by=Clock()),))


def test_先に進んだ帳簿には書けない(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """楽観ロックは adapters の中——黙って上書きしない。"""
    db = tmp_path / "ichiza.db"
    甲, 乙 = SqliteJobs(open_ledger(db)), SqliteJobs(open_ledger(db))
    仕事 = make_job(AwaitingApproval(assignee=Owner(person=座長)), result_at="r://1")
    甲.save(仕事, (JobHandedOut(at=いま, by=Clock()),))
    a = 甲.load(仕事.id)
    b = 乙.load(仕事.id)
    assert a is not None and b is not None
    次, 出来事 = approve(a, by=座長, now=いま)
    甲.save(次, (出来事,))
    次2, 出来事2 = approve(b, by=座長, now=いま)
    with pytest.raises(RuntimeError, match="読み直して"):
        乙.save(次2, (出来事2,))


def test_無い仕事は_None(tmp_path) -> None:  # type: ignore[no-untyped-def]
    帳簿 = _帳簿(tmp_path)
    仕事 = make_job(Ready())
    assert 帳簿.load(仕事.id) is None
