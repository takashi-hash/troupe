"""仕事の帳簿（SQLite）の壊しかた。I1・I3・楽観ロック・再構成。"""

from __future__ import annotations

from datetime import UTC, datetime

from adapters.ledger.db import open_ledger
from adapters.ledger.jobs import SqliteJobs
from domain.aggregates.job.approve import approve
from domain.aggregates.job.life import AwaitingApproval, Ready
from domain.events.job.job_handed_out import JobHandedOut
from domain.value_objects.people.clock import Clock
from domain.value_objects.people.owner import Owner
from tests.aggregates.job.conftest import make_job, 座長

いま = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


import pytest


@pytest.fixture
def 帳簿(tmp_path):  # type: ignore[no-untyped-def]
    conn = open_ledger(tmp_path / "ichiza.db")
    yield SqliteJobs(conn)
    conn.close()


def test_積んで読み直すと同じ姿が返る(帳簿) -> None:  # type: ignore[no-untyped-def]
    仕事 = make_job(Ready())
    帳簿.save(仕事, (JobHandedOut(at=いま, by=Clock()),))
    assert 帳簿.load(仕事.id) == 仕事


def test_出来事なしでは書けない(帳簿) -> None:  # type: ignore[no-untyped-def]
    """I1 — 書き込みの門。"""
    with pytest.raises(ValueError, match="I1"):
        帳簿.save(make_job(Ready()), ())


def test_同じ作成元の仕事は二度書けない(帳簿) -> None:  # type: ignore[no-untyped-def]
    """I3 — 帳簿の一意の鍵。"""
    帳簿.save(make_job(Ready()), (JobHandedOut(at=いま, by=Clock()),))
    from domain.value_objects.job.job_id import JobId

    同じ作成元 = make_job(Ready(), id=JobId(text="J-0002"))
    with pytest.raises(ValueError, match="I3"):
        帳簿.save(同じ作成元, (JobHandedOut(at=いま, by=Clock()),))


def test_先に進んだ帳簿には書けない(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """楽観ロックは adapters の中——黙って上書きしない。"""
    db = tmp_path / "ichiza.db"
    conn甲, conn乙 = open_ledger(db), open_ledger(db)
    甲, 乙 = SqliteJobs(conn甲), SqliteJobs(conn乙)
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
    conn甲.close()
    conn乙.close()


def test_無い仕事は_None(帳簿) -> None:  # type: ignore[no-untyped-def]
    仕事 = make_job(Ready())
    assert 帳簿.load(仕事.id) is None
