"""帳簿の器 — 表の形と、開きかた。**手元は SQLite、クラウドは Cloud SQL（Postgres）。**

設計: 設計/どう作るか §5「帳簿の実装は手元（SQLite）とクラウド（Cloud SQL）、口は1つ」・
§4「ロック——楽観ロックは adapters の中に隠す」・
仕事とは何か §5 I3「同じ作成元から仕事は二度作られない——帳簿の一意の鍵」・
I10「帳簿は自分の形を名乗り、合わなければ開かない」。

**起きたことと、いまの姿を持つ場。書き換えない・消さない**——
出来事は積むだけの表、姿は置き換えの表（履歴は出来事が持つ）。

**表の形は1つ**（`_TABLES`）。器ごとに違うのは採番の書きかただけ——
形を2枚に分けると、片方だけ直して離れていく。

**帳簿は自分の語で名乗る**（`LedgerDuplicate`）。
一意の鍵に弾かれたことを外の道具の例外（`sqlite3.IntegrityError`・
`psycopg.errors.UniqueViolation`）のまま上へ渡すと、**書き込みの門が器を知ることになる**。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Protocol, Sequence

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
    at {採番},
    job_id TEXT NOT NULL,
    body TEXT NOT NULL
);
"""


class LedgerDuplicate(Exception):
    """同じ鍵の行が既にある — **一意の鍵が拒んだ**（I3 の最後の砦）。

    器がどちらでも、上に届くのはこの1つ。**書き込みの門は器を知らない。**
    """


class Cursor(Protocol):
    """引いた結果への口。**帳簿が返すのはこれだけ。**"""

    @property
    def rowcount(self) -> int: ...

    def fetchone(self) -> Any: ...

    def fetchall(self) -> list[Any]: ...


class Ledger(Protocol):
    """帳簿への口。**実装は手元とクラウドの2つ、口は1つ。**

    渡す SQL は `?` で書く——器ごとの書きかたの違いは、この下で吸う。
    """

    def execute(self, sql: str, parameters: Sequence[Any] = (), /) -> Cursor: ...

    def commit(self) -> None: ...

    def close(self) -> None: ...

    @property
    def in_transaction(self) -> bool: ...


def _文ごと(script: str) -> list[str]:
    """表の形を1文ずつに割る。**器によらず同じ形が立つ**ことの担保。"""
    return [文.strip() for 文 in script.split(";") if 文.strip()]


def _形を検める(ledger: Ledger) -> None:
    """形の番号を名乗らせ、合わなければ開かない（I10）。"""
    row = ledger.execute("SELECT number FROM shape").fetchone()
    if row is None:
        ledger.execute("INSERT INTO shape(number) VALUES (?)", (SHAPE,))
        ledger.commit()
        return
    if row[0] != SHAPE:
        ledger.close()
        raise RuntimeError(
            f"帳簿の形が合いません（帳簿は {row[0]}、コードは {SHAPE}）。読めない、入れ直せ"
        )


class _SqliteLedger:
    """手元の帳簿 — SQLite。1つのファイルに全部が在る。"""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, parameters: Sequence[Any] = (), /) -> Cursor:
        try:
            return self._conn.execute(sql, parameters)
        except sqlite3.IntegrityError as なぜ:
            raise LedgerDuplicate(str(なぜ)) from なぜ

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @property
    def in_transaction(self) -> bool:
        return self._conn.in_transaction


def _置き換える(sql: str) -> str:
    """`?` を `%s` へ。**引用符の中は触らない**——SQL の文字列の中の `?` は値ではない。"""
    out: list[str] = []
    引用符の中 = False
    for 文字 in sql:
        if 文字 == "'":
            引用符の中 = not 引用符の中
        out.append("%s" if 文字 == "?" and not 引用符の中 else 文字)
    return "".join(out)


class _PostgresLedger:
    """クラウドの帳簿 — Cloud SQL（Postgres）。

    **自動確定で開く。** 一座は「BEGIN IMMEDIATE …… COMMIT」と自分で書く
    （楽観ロックの窓を自分で閉じるため）ので、器が勝手に取引を開くと二重になる。
    `BEGIN IMMEDIATE` は SQLite の書きかた——ここで `BEGIN` に直す。
    """

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    def execute(self, sql: str, parameters: Sequence[Any] = (), /) -> Cursor:
        import psycopg

        文 = "BEGIN" if sql.strip().upper() == "BEGIN IMMEDIATE" else _置き換える(sql)
        try:
            return self._conn.execute(文, tuple(parameters))
        except psycopg.errors.UniqueViolation as なぜ:
            raise LedgerDuplicate(str(なぜ)) from なぜ

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @property
    def in_transaction(self) -> bool:
        import psycopg

        return self._conn.info.transaction_status != psycopg.pq.TransactionStatus.IDLE


def open_ledger(path: Path | str) -> Ledger:
    """手元の帳簿を開く。無ければ形を作り、形の番号が合わなければ開かない（I10）。"""
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    # 常駐で時計と AI が同時に書く。待たずに即エラーにせず、少し待つ
    # （楽観ロックは別の層の話——これは器の混雑の話）
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    ledger = _SqliteLedger(conn)
    for 文 in _文ごと(_TABLES.replace("{採番}", "INTEGER PRIMARY KEY AUTOINCREMENT")):
        ledger.execute(文)
    _形を検める(ledger)
    return ledger


def open_cloud_ledger(dsn: str) -> Ledger:
    """クラウドの帳簿を開く。**開きかた以外は手元と同じ**——形も、形の検めも。

    在りかは接続の文字（Cloud SQL の接続名か、ホストと名前）。
    **注ぐのは main.py だけ**——ここを呼ぶ者は器を選んでいるのであって、業務を知らない。
    """
    import psycopg

    # 一座は取引を自分で開け閉めする（`BEGIN IMMEDIATE` …… `COMMIT`）。
    # 器に任せると取引が二重になり、楽観ロックの窓が閉じない。
    conn = psycopg.connect(dsn, autocommit=True)
    ledger = _PostgresLedger(conn)
    for 文 in _文ごと(_TABLES.replace("{採番}", "BIGSERIAL PRIMARY KEY")):
        ledger.execute(文)
    _形を検める(ledger)
    return ledger
