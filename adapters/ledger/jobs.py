"""仕事の帳簿 — `JobRepository` の SQLite 実装。**書き込みの門。**

設計: 設計/仕事が回る筋道.md §3・§4、不変条件 I1・I3。

- **姿と出来事を同じトランザクションで積む**（I1 の最終執行者）。出来事が空なら拒む
- **同じ作成元から二度作らない**は表の一意の鍵が拒む（I3）
- 楽観ロックはここに隠す——読んだときの改訂番号を覚え、書くとき比べる。
  先に誰かが書いていたら「読み直せ」と止まる（黙って上書きしない）
- 再構成に効かせるのは**型の形だけ**——きのうの行をきょうの規則で弾かない
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from pydantic import TypeAdapter

from domain.aggregates.job.job import Job
from domain.aggregates.job.life import State
from domain.events.event import Event
from domain.value_objects.job.job_id import JobId

_STATE: TypeAdapter[Any] = TypeAdapter(State)
_JOB: TypeAdapter[Any] = TypeAdapter(Job[State])


def dump_job(job: Job[Any]) -> str:
    return job.model_dump_json()


def load_job(body: str) -> Job[Any]:
    return _JOB.validate_json(body)


class SqliteJobs:
    """仕事の帳簿。1つの接続の上で、読んだ改訂を覚える。"""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._seen: dict[str, int] = {}

    def load(self, id: JobId) -> Job[Any] | None:
        row = self._conn.execute(
            "SELECT revision, body FROM jobs WHERE id = ?", (id.text,)
        ).fetchone()
        if row is None:
            return None
        self._seen[id.text] = int(row[0])
        return load_job(row[1])

    def save(self, job: Job[Any], events: tuple[Event, ...]) -> None:
        if not events:
            raise ValueError("出来事なしで状態は書けません（I1）")
        state = job.state
        assignee = getattr(state, "assignee", None)
        cur = self._conn
        try:
            cur.execute("BEGIN IMMEDIATE")
            known = self._seen.get(job.id.text)
            if known is None and cur.execute(
                "SELECT 1 FROM jobs WHERE id = ?", (job.id.text,)
            ).fetchone():
                raise RuntimeError("帳簿が先に進んでいます。読み直してください")
            if known is None:
                cur.execute(
                    "INSERT INTO jobs(id, revision, origin, state_name, assignee_name,"
                    " rule_name, period, body) VALUES (?, 1, ?, ?, ?, ?, ?, ?)",
                    (
                        job.id.text,
                        job.origin.key,
                        type(state).__name__,
                        _name_of(assignee),
                        job.born_of.text if job.born_of else None,
                        job.period.text if job.period else None,
                        dump_job(job),
                    ),
                )
            else:
                done = cur.execute(
                    "UPDATE jobs SET revision = revision + 1, state_name = ?,"
                    " assignee_name = ?, body = ? WHERE id = ? AND revision = ?",
                    (
                        type(state).__name__,
                        _name_of(assignee),
                        dump_job(job),
                        job.id.text,
                        known,
                    ),
                )
                if done.rowcount != 1:
                    raise RuntimeError("帳簿が先に進んでいます。読み直してください")
            seq = cur.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM job_events WHERE job_id = ?",
                (job.id.text,),
            ).fetchone()[0]
            for i, event in enumerate(events, start=1):
                cur.execute(
                    "INSERT INTO job_events(job_id, seq, name, at, by_kind, by_name, body)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        job.id.text,
                        seq + i,
                        type(event).__name__,
                        event.at.isoformat(),
                        event.by.kind,
                        _name_of(event.by),
                        event.model_dump_json(),
                    ),
                )
            cur.execute("COMMIT")
        except sqlite3.IntegrityError as なぜ:
            cur.execute("ROLLBACK")
            raise ValueError(f"同じ作成元の仕事が既にあります（I3）: {なぜ}") from なぜ
        except BaseException:
            if cur.in_transaction:
                cur.execute("ROLLBACK")
            raise
        self._seen[job.id.text] = (known or 0) + 1


def _name_of(who: object | None) -> str | None:
    """担当・起こす者の名。受け持ちの人（`Owner`）は中の人の名で数える。"""
    person = getattr(who, "person", None)
    if person is not None:
        who = person
    name = getattr(who, "name", None)
    return str(name) if name is not None else None


def read_events(conn: sqlite3.Connection, id: JobId) -> tuple[tuple[str, str], ...]:
    """出来事の（名, 中身の JSON）の列。読みの部品——履歴と材料が使う。"""
    rows = conn.execute(
        "SELECT name, body FROM job_events WHERE job_id = ? ORDER BY seq", (id.text,)
    ).fetchall()
    return tuple((str(n), str(b)) for n, b in rows)


def event_bodies(conn: sqlite3.Connection, id: JobId, name: str) -> tuple[dict[str, Any], ...]:
    """ある名の出来事の中身。"""
    return tuple(
        json.loads(b) for n, b in read_events(conn, id) if n == name
    )
