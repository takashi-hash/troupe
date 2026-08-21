"""dispatch の輪のテスト — Gate（freeze 前は配らない）と Briefing 詰めの確認。"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from adapters.sqlite_ledger import SqliteLedger
from app.manager import create, dispatch
from domain.board import Board, Constitution, freeze
from domain.definition import Definition, Version
from domain.event import Event
from domain.job import Budget, Ready

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)


def seed_definition(ledger: SqliteLedger) -> None:
    definition = Definition(
        name="週次の検査の見張り",
        board_id="ボード/運転",
        versions=(
            Version(
                number=1,
                instruction="検査が緑かを確かめ、赤があれば何が壊れたかを書く",
                acceptance="検査の結果が引用されている",
                cadence="weekly",
                deadline_days=2,
                budget=Budget(calls=20, seconds=600),
                source_refs=("読み口/検査の結果",),
            ),
        ),
        enacted=1,
    )
    ledger.definitions.put(
        definition,
        [Event(kind="VersionAppended", at=NOW), Event(kind="DefinitionEnacted", at=NOW)],
    )


def seed_board(ledger: SqliteLedger, do_freeze: bool) -> None:
    board = Board(
        board_id="ボード/運転",
        constitutions=(
            Constitution(
                number=1,
                purpose="Ichiza 自身の運転を回す",
                non_goals="診療の中身には触れない",
                acceptance="Evidence で閉じられること",
                vocabulary="リポジトリ・依存・バックアップ先",
            ),
        ),
    )
    events = [Event(kind="ConstitutionAppended", at=NOW)]
    if do_freeze:
        board = freeze(board, 1)
        events.append(Event(kind="ConstitutionFrozen", at=NOW))
    ledger.boards.put(board, events)


@pytest.fixture
def ledger(tmp_path: Path) -> SqliteLedger:
    return SqliteLedger(tmp_path / "ledger.db")


def test_gate_blocks_dispatch_before_freeze(ledger: SqliteLedger) -> None:
    """freeze 前は配らない——Gate は閉じている"""
    seed_definition(ledger)
    seed_board(ledger, do_freeze=False)
    (job_id,) = create(ledger, NOW)
    assert dispatch(ledger, NOW) == []
    got = ledger.jobs.get(job_id)
    assert got is not None and got[0].state.kind == "Created"


def test_dispatch_after_freeze_fills_briefing(ledger: SqliteLedger) -> None:
    """freeze 後に配られ、Briefing は参照で満たされる（業務ルール・受け入れ基準・方針・使用上限）"""
    seed_definition(ledger)
    seed_board(ledger, do_freeze=True)
    (job_id,) = create(ledger, NOW)
    assert dispatch(ledger, NOW) == [job_id]
    got = ledger.jobs.get(job_id)
    assert got is not None
    job, _ = got
    assert isinstance(job.state, Ready)
    briefing = job.state.briefing
    assert briefing.definition_ref == "業務ルール/週次の検査の見張り/1"
    assert briefing.acceptance_ref == "業務ルール/週次の検査の見張り/1#受け入れ基準"
    assert briefing.constitution_ref == "ボード/運転/方針/1"
    assert briefing.source_refs == ("読み口/検査の結果",)
    assert briefing.budget == Budget(calls=20, seconds=600)
    rows = ledger._con.execute(
        "SELECT COUNT(*) FROM events WHERE kind='JobDispatched'"
    ).fetchone()
    assert rows[0] == 1


def test_dispatch_is_idempotent(ledger: SqliteLedger) -> None:
    """2周目は何も配らない——Ready は Created ではない"""
    seed_definition(ledger)
    seed_board(ledger, do_freeze=True)
    create(ledger, NOW)
    dispatch(ledger, NOW)
    assert dispatch(ledger, NOW) == []
