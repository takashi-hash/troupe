"""注入のテスト — カスタムのデータが帳簿に入り、2度目は何もしない（冪等）。

土台はカスタムの中身を1行も知らない——読むのは方針と業務ルールという型だけ。
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from adapters.sqlite_ledger import SqliteLedger
from adapters.toml_custom import TomlCustom
from app.human import inject

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
BY = "人/座長"


@pytest.fixture
def ledger(tmp_path: Path) -> SqliteLedger:
    return SqliteLedger(tmp_path / "ledger.db")


def custom(folder: Path, versions: int = 1) -> TomlCustom:
    """題材のフォルダを1つ書く（現場が書くデータの体）"""
    (folder / "rules").mkdir(parents=True, exist_ok=True)
    (folder / "board.toml").write_text(
        'board_id = "ボード/試し"\n\n'
        "[[constitutions]]\nnumber = 1\n"
        'purpose = "試す"\nnon_goals = "ほかはしない"\n'
        'acceptance = "根拠で閉じる"\nvocabulary = "試しの言葉"\n',
        encoding="utf-8",
    )
    body = 'name = "週次の見張り"\nboard_id = "ボード/試し"\n'
    for number in range(1, versions + 1):
        body += (
            f"\n[[versions]]\nnumber = {number}\n"
            f'instruction = "v{number} のやること"\nacceptance = "引用がある"\n'
            'cadence = "weekly"\ndeadline_days = 3\n'
            "budget_calls = 20\nbudget_seconds = 600\n"
            'source_refs = ["読み口/試し"]\nmust_contain = ["引用"]\n'
        )
    (folder / "rules" / "週次の見張り.toml").write_text(body, encoding="utf-8")
    return TomlCustom(folder)


def test_injection_creates_board_and_definition(ledger: SqliteLedger, tmp_path: Path) -> None:
    """帳簿が空でも、注入だけでボードと業務ルールが立つ"""
    touched = inject(ledger, custom(tmp_path / "試し"), BY, NOW)
    assert touched == ["ボード/試し", "週次の見張り"]
    board = ledger.boards.get("ボード/試し")
    assert board is not None and board.frozen == 1  # 凍結まで（人がこの操作を走らせた）
    definition = ledger.definitions.get("週次の見張り")
    assert definition is not None and definition.enacted == 1


def test_injection_is_idempotent(ledger: SqliteLedger, tmp_path: Path) -> None:
    """2度目は何もしない——版は積むだけなので、増えていなければ積まない"""
    source = custom(tmp_path / "試し")
    inject(ledger, source, BY, NOW)
    assert inject(ledger, source, BY, NOW) == []


def test_injection_appends_new_version_only(ledger: SqliteLedger, tmp_path: Path) -> None:
    """版が増えたら、増えたぶんだけ積んで有効化する（前の版は消えない）"""
    folder = tmp_path / "試し"
    inject(ledger, custom(folder), BY, NOW)
    touched = inject(ledger, custom(folder, versions=2), BY, NOW)
    assert touched == ["週次の見張り"]
    definition = ledger.definitions.get("週次の見張り")
    assert definition is not None
    assert len(definition.versions) == 2 and definition.enacted == 2
    assert definition.versions[0].instruction == "v1 のやること"  # 前の版は消えない


def test_who_enacted_is_recorded(ledger: SqliteLedger, tmp_path: Path) -> None:
    """誰が有効化したかは出来事に残る（I5「説明できる」）"""
    inject(ledger, custom(tmp_path / "試し"), BY, NOW)
    rows = ledger._con.execute(
        "SELECT payload FROM events WHERE kind='DefinitionEnacted'"
    ).fetchall()
    assert len(rows) == 1
    assert BY in rows[0][0]


def test_foundation_does_not_know_the_topic(tmp_path: Path) -> None:
    """土台は題材の中身を知らない——読むのは方針と業務ルールという型だけ"""
    board, definitions = custom(tmp_path / "試し").load()
    assert board.board_id == "ボード/試し"
    assert board.frozen is None  # 凍結も有効化もされていない形で返る
    assert definitions[0].enacted is None
