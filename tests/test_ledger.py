"""帳簿の保存のテスト — 設計/8_保存/帳簿の保存.md §5 の表を1行=1テストで写す。"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from adapters.sqlite_ledger import SqliteLedger, StaleLedger
from domain.event import Event, EventKind
from domain.job import (
    Briefing,
    Budget,
    Core,
    Created,
    FromDefinition,
    IllegalTransition,
    Job,
    Lease,
    MissingEvent,
    Ready,
    Running,
    origin_key,
)

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)


def briefing_example() -> Briefing:
    return Briefing(
        definition_ref="業務ルール/週次の検査の見張り/3",
        source_refs=(),
        material_refs=(),
        artifact_slot="成果物/週次の検査の見張り/2026-W34",
        acceptance_ref="業務ルール/週次の検査の見張り/3#基準",
        budget=Budget(calls=50, seconds=3600),
        constitution_ref="ボード/運転/方針/1",
    )


def job_example(job_id: str = "タスク-001", period: str = "2026-W34") -> Job:
    return Job(
        core=Core(
            job_id=job_id,
            origin=FromDefinition(definition_name="週次の検査の見張り", version=3, period=period),
            board_id="ボード/運転",
            ready_at=NOW,
            deadline=NOW + timedelta(days=9),
            budget=Budget(calls=50, seconds=3600),
        ),
        state=Created(),
    )


def ready(job: Job) -> Job:
    return Job(core=job.core, state=Ready(briefing=briefing_example()))


def event(kind: EventKind, job_id: str) -> Event:
    return Event(kind=kind, at=NOW, job_id=job_id)


@pytest.fixture
def ledger(tmp_path: Path) -> SqliteLedger:
    return SqliteLedger(tmp_path / "ledger.db")


def test_put_then_get_roundtrip(ledger: SqliteLedger) -> None:
    """書き込んだ Job がそのまま読み出せる"""
    job = job_example()
    assert ledger.jobs.put(job, expected_rev=0, events=[event("JobCreated", job.core.job_id)])
    assert ledger.jobs.get(job.core.job_id) == (job, 1)


def test_append_only_rejects_update_and_delete(ledger: SqliteLedger) -> None:
    """AppendOnlyLog は UPDATE / DELETE をトリガが拒否する——積むだけ"""
    ledger.events.append([event("UtteranceLogged", "タスク-001")])
    with pytest.raises(sqlite3.DatabaseError):
        ledger._con.execute("UPDATE events SET kind='x'")
    with pytest.raises(sqlite3.DatabaseError):
        ledger._con.execute("DELETE FROM events")


def test_origin_unique_kills_duplicate_creation(ledger: SqliteLedger) -> None:
    """同じ Origin の Job は二度作成されない——作成元の鍵の一意索引"""
    ledger.jobs.put(job_example("タスク-001"), expected_rev=0, events=[event("JobCreated", "タスク-001")])
    duplicate = job_example("タスク-002")  # id は別・Origin は同じ
    with pytest.raises(sqlite3.IntegrityError):
        ledger.jobs.put(duplicate, expected_rev=0, events=[event("JobCreated", "タスク-002")])
    rows = ledger._con.execute("SELECT COUNT(*) FROM events WHERE kind='JobCreated'").fetchone()
    assert rows[0] == 1  # JobCreated は1つだけ（原子性: 負けた側の Event も残らない）


def test_find_by_origin(ledger: SqliteLedger) -> None:
    """作成元で探す——create の冪等の要"""
    job = job_example()
    key = origin_key(job.core.origin)
    assert key is not None
    assert ledger.jobs.find_by_origin(key) is None
    ledger.jobs.put(job, expected_rev=0, events=[event("JobCreated", job.core.job_id)])
    assert ledger.jobs.find_by_origin(key) == job.core.job_id


def test_optimistic_lock_only_one_wins(ledger: SqliteLedger) -> None:
    """取り合いは版で決着——片方だけ勝つ"""
    job = job_example()
    ledger.jobs.put(job, expected_rev=0, events=[event("JobCreated", job.core.job_id)])
    dispatched = [event("JobDispatched", job.core.job_id)]
    assert ledger.jobs.put(ready(job), expected_rev=1, events=dispatched) is True
    assert ledger.jobs.put(ready(job), expected_rev=1, events=dispatched) is False  # 負け


def test_atomicity_losing_put_leaves_no_event(ledger: SqliteLedger) -> None:
    """負けた書き込みは Event も残さない——1トランザクション"""
    job = job_example()
    ledger.jobs.put(job, expected_rev=0, events=[event("JobCreated", job.core.job_id)])
    lost = ledger.jobs.put(ready(job), expected_rev=99, events=[event("JobDispatched", job.core.job_id)])
    assert lost is False
    rows = ledger._con.execute("SELECT COUNT(*) FROM events").fetchone()
    assert rows[0] == 1  # JobCreated だけ。負けた JobDispatched は残らない


def test_transition_without_its_event_is_rejected(ledger: SqliteLedger) -> None:
    """遷移したのに Event が無い書き込みは拒否——画面が嘘をつかない（put は遷移の門）"""
    job = job_example()
    ledger.jobs.put(job, expected_rev=0, events=[event("JobCreated", job.core.job_id)])
    with pytest.raises(MissingEvent):
        ledger.jobs.put(ready(job), expected_rev=1, events=[])


def test_illegal_transition_is_rejected(ledger: SqliteLedger) -> None:
    """遷移表に無い移りは書けない——Created から Running へは飛べない"""
    job = job_example()
    ledger.jobs.put(job, expected_rev=0, events=[event("JobCreated", job.core.job_id)])
    running = Job(
        core=job.core,
        state=Running(
            briefing=briefing_example(),
            lease=Lease(holder="機体-A", expires_at=NOW),
            retries_left=3,
        ),
    )
    with pytest.raises(IllegalTransition):
        ledger.jobs.put(running, expected_rev=1, events=[event("LeaseTaken", job.core.job_id)])


def test_type_guard_on_load(ledger: SqliteLedger) -> None:
    """DB の state を直接壊しても、戻すときの型が弾く——禁止状態は保存にも効く。

    2026-08-21（段C）から、外に出るのは `StaleLedger`——「いまの型で読めない」と
    名乗って止まる。元の悲鳴は原因として繋がっているので、追える。
    """
    job = job_example()
    ledger.jobs.put(job, expected_rev=0, events=[event("JobCreated", job.core.job_id)])
    broken = '{"core": null, "state": {"kind": "Applied", "artifact_ref": "x"}}'
    ledger._con.execute("UPDATE jobs SET state=? WHERE id=?", (broken, job.core.job_id))
    with pytest.raises(StaleLedger) as caught:
        ledger.jobs.get(job.core.job_id)
    assert isinstance(caught.value.__cause__, ValidationError)
