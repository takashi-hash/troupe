"""帳簿の器の壊しかた。設計/どう作るか §5——**実装は手元とクラウドの2つ、口は1つ**。

Postgres は起こさない——器に依らない部分（表の形・`?` の置き換え・取引の書きかた・
形の検め・一意の鍵の名乗り）だけをここで見る。
**本物の Postgres を通すのは `test_week_a.py`**（`ICHIZA_PG_DSN` が在るときだけ）。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from adapters.ledger.db import (
    SHAPE,
    Ledger,
    LedgerDuplicate,
    _PostgresLedger,
    _置き換える,
    _文ごと,
    _TABLES,
    open_ledger,
)


def test_手元の帳簿は口を名乗れる(tmp_path: Path) -> None:
    帳簿: Ledger = open_ledger(tmp_path / "ichiza.db")
    assert 帳簿.execute("SELECT number FROM shape").fetchone()[0] == SHAPE
    帳簿.close()


def test_形が合わなければ開かない(tmp_path: Path) -> None:
    """I10 — 帳簿は自分の形を名乗り、合わなければ開かない。"""
    道 = tmp_path / "ichiza.db"
    open_ledger(道).close()
    conn = sqlite3.connect(str(道))
    conn.execute("UPDATE shape SET number = ?", (SHAPE + 1,))
    conn.commit()
    conn.close()
    with pytest.raises(RuntimeError, match="帳簿の形が合いません"):
        open_ledger(道)


def test_一意の鍵に弾かれたら帳簿の語で名乗る(tmp_path: Path) -> None:
    """**書き込みの門は器を知らない**——外の道具の例外はここで中の語になる（I3）。"""
    帳簿 = open_ledger(tmp_path / "ichiza.db")
    行 = ("J-1", 1, "同じ作成元", "作られた", None, None, None, "{}")
    入れる = (
        "INSERT INTO jobs(id, revision, origin, state_name, assignee_name,"
        " rule_name, period, body) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    帳簿.execute(入れる, 行)
    with pytest.raises(LedgerDuplicate):
        帳簿.execute(入れる, ("J-2",) + 行[1:])
    帳簿.close()


# --- 表の形は1つ。器ごとに違うのは採番の書きかただけ ---


def test_表の形は採番のところだけが器で変わる() -> None:
    手元 = _TABLES.replace("{採番}", "INTEGER PRIMARY KEY AUTOINCREMENT")
    雲 = _TABLES.replace("{採番}", "BIGSERIAL PRIMARY KEY")
    assert "{採番}" not in 手元 and "{採番}" not in 雲
    assert len(_文ごと(手元)) == len(_文ごと(雲))
    # 差は採番の2文（成果・根拠）だけ——形が2枚に分かれていない証拠
    違う = [甲 for 甲, 乙 in zip(_文ごと(手元), _文ごと(雲)) if 甲 != 乙]
    assert len(違う) == 2
    assert "results" in 違う[0] and "evidence" in 違う[1]


def test_表の形は1文ずつに割れる() -> None:
    """器によらず同じ順で同じ数の文が立つ。空文を混ぜない。"""
    形 = _TABLES.replace("{採番}", "BIGSERIAL PRIMARY KEY")
    文たち = _文ごと(形)
    assert all(文.upper().startswith("CREATE TABLE") for 文 in 文たち)
    # 表の途中の `;` で割れていたら、この数が合わなくなる（数の正本は `_TABLES`）
    assert len(文たち) == 形.count("CREATE TABLE")


# --- `?` の置き換え ---


def test_置き場は全部_パーセントs_になる() -> None:
    assert _置き換える("SELECT 1 FROM jobs WHERE id = ? AND revision = ?") == (
        "SELECT 1 FROM jobs WHERE id = %s AND revision = %s"
    )


def test_引用符の中の疑問符は値ではない() -> None:
    """SQL の文字列の中の `?` を置き換えたら、書いた文の意味が変わる。"""
    assert _置き換える("SELECT '？' , 'a?b' FROM jobs WHERE id = ?") == (
        "SELECT '？' , 'a?b' FROM jobs WHERE id = %s"
    )


def test_絞り込みの組み立てた文も置き換わる() -> None:
    """`IN (?, ?, ?)` は文字で組み立てられる——組み立てたあとに置き換える。"""
    置かない = ", ".join("?" for _ in range(3))
    assert _置き換える(f"SELECT id FROM jobs WHERE state_name NOT IN ({置かない})") == (
        "SELECT id FROM jobs WHERE state_name NOT IN (%s, %s, %s)"
    )


# --- 取引の書きかた ---


class _偽の口:
    """Postgres の接続のふり。渡った文だけを覚える。"""

    def __init__(self) -> None:
        self.文たち: list[str] = []
        self.値たち: list[tuple[Any, ...]] = []

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        self.文たち.append(sql)
        self.値たち.append(params)
        return None


def test_手元の書きかたの取引開始はクラウドの書きかたに直る() -> None:
    """`BEGIN IMMEDIATE` は SQLite の書きかた。**器の違いはここで吸う。**"""
    口 = _偽の口()
    _PostgresLedger(口).execute("BEGIN IMMEDIATE")
    assert 口.文たち == ["BEGIN"]


def test_取引の締めはそのまま渡る() -> None:
    口 = _偽の口()
    帳簿 = _PostgresLedger(口)
    帳簿.execute("COMMIT")
    帳簿.execute("ROLLBACK")
    assert 口.文たち == ["COMMIT", "ROLLBACK"]


def test_渡す値は組になる() -> None:
    """並びのまま渡すと器が受け取らないことがある——組に揃えてから渡す。"""
    口 = _偽の口()
    _PostgresLedger(口).execute("SELECT 1 FROM jobs WHERE id = ?", ["J-1"])
    assert 口.値たち == [("J-1",)]
