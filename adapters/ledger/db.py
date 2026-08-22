"""帳簿の器 — SQLite の表の形と、開きかた。

設計: 設計/どう作るか §4「ロック——楽観ロックは adapters の中に隠す」・
仕事とは何か §5 I3「同じ作成元から仕事は二度作られない——帳簿の一意の鍵」・
I10「帳簿は自分の形を名乗り、合わなければ開かない」。

**起きたことと、いまの姿を持つ場。書き換えない・消さない**——
出来事は積むだけの表、姿は置き換えの表（履歴は出来事が持つ）。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

#: 帳簿の形の番号。形を変えたら上げる——合わなければ開かない（I10）。
SHAPE = 1

_TABLES = """
CREATE TABLE IF NOT EXISTS shape(number INTEGER NOT NULL);

CREATE TABLE IF NOT EXISTS jobs(
    id TEXT PRIMARY KEY,
    revision INTEGER NOT NULL,
    origin TEXT NOT NULL UNIQUE,          -- I3 同じ作成元から二度作られない（一意の鍵）
    state_name TEXT NOT NULL,             -- 読みのための写し。正本は body
    assignee_name TEXT,
    rule_name TEXT,
    period TEXT,
    body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_events(
    job_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    name TEXT NOT NULL,
    at TEXT NOT NULL,
    by_kind TEXT NOT NULL,
    by_name TEXT,
    body TEXT NOT NULL,
    PRIMARY KEY(job_id, seq)
);

CREATE TABLE IF NOT EXISTS rules(
    name TEXT PRIMARY KEY,
    revision INTEGER NOT NULL,
    body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rule_events(
    rule_name TEXT NOT NULL,
    seq INTEGER NOT NULL,
    name TEXT NOT NULL,
    at TEXT NOT NULL,
    by_kind TEXT NOT NULL,
    by_name TEXT,
    body TEXT NOT NULL,
    PRIMARY KEY(rule_name, seq)
);

CREATE TABLE IF NOT EXISTS results(
    at TEXT PRIMARY KEY,
    body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence(
    at TEXT PRIMARY KEY,
    body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions(
    at TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT
);

CREATE TABLE IF NOT EXISTS assessments(
    at INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    body TEXT NOT NULL
);
"""


def open_ledger(path: Path | str) -> sqlite3.Connection:
    """帳簿を開く。無ければ形を作り、形の番号が合わなければ開かない（I10）。"""
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_TABLES)
    row = conn.execute("SELECT number FROM shape").fetchone()
    if row is None:
        conn.execute("INSERT INTO shape(number) VALUES (?)", (SHAPE,))
        conn.commit()
    elif row[0] != SHAPE:
        conn.close()
        raise RuntimeError(
            f"帳簿の形が合いません（帳簿は {row[0]}、コードは {SHAPE}）。読めない、入れ直せ"
        )
    return conn
