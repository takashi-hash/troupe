"""create の輪のテスト — 設計/5_出来事/調停図.md §2 の冪等表を1行=1テストで写す。"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from adapters.sqlite_ledger import SqliteLedger
from app.manager import create
from domain.definition import Definition, Version
from domain.event import Event
from domain.job import Budget

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)


def seed(ledger: SqliteLedger, definition: Definition) -> None:
    events = [Event(kind="VersionAppended", at=NOW)]
    if definition.enacted is not None:
        events.append(Event(kind="DefinitionEnacted", at=NOW))
    ledger.definitions.put(definition, events)


def definition_example(name: str = "週次の検査の見張り", enacted: int | None = 1) -> Definition:
    return Definition(
        name=name,
        board_id="ボード/運転",
        versions=(
            Version(
                number=1,
                instruction="検査が緑かを確かめ、赤があれば何が壊れたかを書く",
                acceptance="検査の結果が引用されている。7日より古ければ赤と書く",
                cadence="weekly",
                deadline_days=2,
                budget=Budget(calls=20, seconds=600),
            ),
        ),
        enacted=enacted,
    )


@pytest.fixture
def ledger(tmp_path: Path) -> SqliteLedger:
    return SqliteLedger(tmp_path / "ledger.db")


def test_create_is_idempotent_per_origin(ledger: SqliteLedger) -> None:
    """同じ Definition と期間では二度作成されない——輪を2周回して JobCreated は1件"""
    seed(ledger, definition_example())
    first = create(ledger, NOW)
    second = create(ledger, NOW + timedelta(hours=3))  # 同じ週にもう1周
    assert len(first) == 1
    assert second == []
    rows = ledger._con.execute("SELECT COUNT(*) FROM events WHERE kind='JobCreated'").fetchone()
    assert rows[0] == 1


def test_not_enacted_definition_creates_nothing(ledger: SqliteLedger) -> None:
    """有効でない Definition からは作成されない——enact するのは Human だけ"""
    seed(ledger, definition_example(enacted=None))
    assert create(ledger, NOW) == []


def test_two_definitions_two_jobs(ledger: SqliteLedger) -> None:
    """Definition が2つなら Job が2つ作成される——名指しの一覧でなく宣言から導く"""
    seed(ledger, definition_example("週次の検査の見張り"))
    seed(ledger, definition_example("週次の依存の棚卸し"))
    assert len(create(ledger, NOW)) == 2


def test_new_period_creates_new_job(ledger: SqliteLedger) -> None:
    """期間が変われば新しい Job が作成される——翌週のタスクは翌週に"""
    seed(ledger, definition_example())
    assert len(create(ledger, NOW)) == 1
    assert len(create(ledger, NOW + timedelta(weeks=1))) == 1
    rows = ledger._con.execute("SELECT COUNT(*) FROM events WHERE kind='JobCreated'").fetchone()
    assert rows[0] == 2


def test_created_job_carries_definition_decisions(ledger: SqliteLedger) -> None:
    """作成済み Job は Definition の決めたもの（使用上限・期限・作成元）を携える"""
    seed(ledger, definition_example())
    (job_id,) = create(ledger, NOW)
    got = ledger.jobs.get(job_id)
    assert got is not None
    job, _ = got
    assert job.state.kind == "Created"
    assert job.core.origin.kind == "FromDefinition"
    assert job.core.budget == Budget(calls=20, seconds=600)
    assert job.core.deadline == NOW + timedelta(days=2)
