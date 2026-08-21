"""業務ルールとボードの門のテスト — 「積むだけ」「必須 Event」に執行者がいることの確認。"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from adapters.sqlite_ledger import SqliteLedger
from domain.board import Board, CannotFreeze, Constitution, freeze
from domain.definition import AppendOnlyViolation, CannotEnact, Definition, Version
from domain.event import Event, EventKind
from domain.job import Budget, MissingEvent

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)


def version(number: int) -> Version:
    return Version(
        number=number,
        instruction=f"やること v{number}",
        acceptance="良しの条件",
        cadence="weekly",
        deadline_days=2,
        budget=Budget(calls=20, seconds=600),
    )


def definition(*numbers: int, enacted: int | None = None) -> Definition:
    return Definition(
        name="週次の検査の見張り",
        board_id="ボード/運転",
        versions=tuple(version(n) for n in numbers),
        enacted=enacted,
    )


def board(frozen: int | None = None) -> Board:
    return Board(
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
        frozen=frozen,
    )


def event(kind: EventKind) -> Event:
    return Event(kind=kind, at=NOW)


@pytest.fixture
def ledger(tmp_path: Path) -> SqliteLedger:
    return SqliteLedger(tmp_path / "ledger.db")


def test_definition_versions_cannot_shrink(ledger: SqliteLedger) -> None:
    """版は積むだけ——減らした業務ルールは書けない（積むだけの破り）"""
    ledger.definitions.put(definition(1, 2), [event("VersionAppended")])
    with pytest.raises(AppendOnlyViolation):
        ledger.definitions.put(definition(1), [event("VersionAppended")])


def test_definition_version_cannot_be_rewritten(ledger: SqliteLedger) -> None:
    """既にある版の書き換えは書けない——上書きは無い"""
    ledger.definitions.put(definition(1), [event("VersionAppended")])
    tampered = definition(1).model_copy(
        update={"versions": (version(1).model_copy(update={"instruction": "書き換え"}),)}
    )
    with pytest.raises(AppendOnlyViolation):
        ledger.definitions.put(tampered, [event("VersionAppended")])


def test_enact_requires_its_event(ledger: SqliteLedger) -> None:
    """enact したのに DefinitionEnacted が無い書き込みは拒否——誰が有効化したかは Event が持つ（I5）"""
    ledger.definitions.put(definition(1), [event("VersionAppended")])
    with pytest.raises(MissingEvent):
        ledger.definitions.put(definition(1, enacted=1), [])


def test_cannot_enact_unknown_version(ledger: SqliteLedger) -> None:
    """存在しない版は有効化できない"""
    with pytest.raises(CannotEnact):
        ledger.definitions.put(
            definition(1, enacted=9),
            [event("VersionAppended"), event("DefinitionEnacted")],
        )


def test_constitution_cannot_be_shrunk(ledger: SqliteLedger) -> None:
    """方針も積むだけ——減らしたボードは書けない"""
    ledger.boards.put(board(), [event("ConstitutionAppended")])
    stripped = board().model_copy(update={"constitutions": ()})
    with pytest.raises(AppendOnlyViolation):
        ledger.boards.put(stripped, [])


def test_freeze_requires_its_event(ledger: SqliteLedger) -> None:
    """freeze したのに ConstitutionFrozen が無い書き込みは拒否"""
    ledger.boards.put(board(), [event("ConstitutionAppended")])
    with pytest.raises(MissingEvent):
        ledger.boards.put(freeze(board(), 1), [])


def test_cannot_freeze_unknown_constitution() -> None:
    """存在しない方針は凍結できない"""
    with pytest.raises(CannotFreeze):
        freeze(board(), 9)
