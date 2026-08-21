"""帳簿の保存 — 口の SQLite 実装（設計/8_保存/帳簿の保存.md の写し）。

- 集約は JSON 1列＋rev（楽観ロック）
- 積むだけの列は UPDATE / DELETE をトリガで拒否（「積むだけ」を DB が強制）
- 書き込みと出来事の追記は1トランザクション（帳簿の原子性）
- jobs.origin_key の一意索引が二重の作成を殺す
- **置き場は集約ルートごと**——帳簿はそれらを差し出す場（口の型と同じ形）
- 接続はスレッドごとに持つ（SQLite の接続はスレッドを跨げない）
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence

from domain.artifact import Artifact
from domain.board import Board, board_required_events
from domain.definition import Definition, definition_required_events
from domain.event import Event
from domain.evidence import Evidence
from domain.job import IllegalTransition, Job, MissingEvent, origin_key, required_events
from domain.participant import Participant

_AGGREGATE_TABLES = (
    "jobs",
    "definitions",
    "boards",
    "participants",
    "proposals",
    "source_registrations",
)
_LOG_TABLES = ("events", "artifacts", "evidences", "utterances")


def _schema() -> str:
    parts: list[str] = ["CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);"]
    for table in _AGGREGATE_TABLES:
        extra = ",\n  origin_key TEXT UNIQUE" if table == "jobs" else ""
        parts.append(
            f"""CREATE TABLE IF NOT EXISTS {table}(
  id TEXT PRIMARY KEY,
  state TEXT NOT NULL,
  rev INTEGER NOT NULL,
  updated_at TEXT NOT NULL{extra}
);"""
        )
    for table in _LOG_TABLES:
        parts.append(
            f"""CREATE TABLE IF NOT EXISTS {table}(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  kind TEXT NOT NULL,
  job_id TEXT,
  payload TEXT NOT NULL
);"""
        )
        # 積むだけ: 書き換え・削除は DB が拒否する（宣言に執行者）
        for verb in ("UPDATE", "DELETE"):
            parts.append(
                f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{verb.lower()}
BEFORE {verb} ON {table}
BEGIN SELECT RAISE(ABORT, 'append only'); END;"""
            )
    parts.append("CREATE INDEX IF NOT EXISTS events_by_job ON events(job_id, seq);")
    parts.append(
        "CREATE INDEX IF NOT EXISTS evidences_by_ref "
        "ON evidences(json_extract(payload, '$.evidence_ref'), seq);"
    )
    parts.append(
        "CREATE INDEX IF NOT EXISTS artifacts_by_ref "
        "ON artifacts(json_extract(payload, '$.artifact_ref'), seq);"
    )
    return "\n".join(parts)


class _Lost(Exception):
    """楽観ロックの負け（内部用）"""


class _Base:
    """置き場の共通の足場——接続と書きトランザクションを分け合う"""

    def __init__(self, ledger: "SqliteLedger") -> None:
        self._ledger = ledger

    @property
    def _con(self) -> sqlite3.Connection:
        return self._ledger.connection

    def _write(self):
        return self._ledger.write()

    def _insert_events(self, events: Sequence[Event]) -> None:
        self._ledger.insert_events(events)

    def _require(self, required: frozenset[str], events: Sequence[Event], where: str) -> None:
        missing = required - {event.kind for event in events}
        if missing:
            raise MissingEvent(f"{where} の書き込みには {sorted(missing)} が要る")


class _Jobs(_Base):
    """タスクの置き場"""

    def get(self, job_id: str) -> tuple[Job, int] | None:
        """読み出す — タスクと rev。禁止状態は読み込みでも弾かれる"""
        row = self._con.execute("SELECT state, rev FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return None
        return Job.model_validate_json(row[0]), int(row[1])

    def put(self, job: Job, expected_rev: int, events: Sequence[Event]) -> bool:
        """書き込む — 遷移の門と楽観ロックを通す。負けたら偽"""
        now = datetime.now(timezone.utc).isoformat()
        state = job.model_dump_json()
        try:
            with self._write():
                self._enforce_transition(job, events)
                if expected_rev == 0:
                    self._con.execute(
                        "INSERT INTO jobs(id, state, rev, updated_at, origin_key) "
                        "VALUES(?,?,1,?,?)",
                        (job.core.job_id, state, now, origin_key(job.core.origin)),
                    )
                else:
                    cur = self._con.execute(
                        "UPDATE jobs SET state=?, rev=rev+1, updated_at=? WHERE id=? AND rev=?",
                        (state, now, job.core.job_id, expected_rev),
                    )
                    if cur.rowcount == 0:
                        raise _Lost()
                self._insert_events(events)
        except _Lost:
            return False
        return True

    def find_by_origin(self, key: str) -> str | None:
        """作成元で探す — 冪等の要"""
        row = self._con.execute("SELECT id FROM jobs WHERE origin_key=?", (key,)).fetchone()
        return None if row is None else str(row[0])

    def find_by_state(self, kind: str) -> tuple[str, ...]:
        """状態で探す — その状態に居るタスクの id たち"""
        rows = self._con.execute(
            "SELECT id FROM jobs WHERE json_extract(state, '$.state.kind')=? ORDER BY id", (kind,)
        ).fetchall()
        return tuple(str(row[0]) for row in rows)

    def _enforce_transition(self, job: Job, events: Sequence[Event]) -> None:
        """書き込みは遷移の門——遷移表に無い移りと、必須の出来事の欠けを拒否する"""
        row = self._con.execute(
            "SELECT state FROM jobs WHERE id=?", (job.core.job_id,)
        ).fetchone()
        old_kind: str | None = None
        if row is not None:
            old_kind = json.loads(row[0])["state"]["kind"]
        new_kind = job.state.kind
        required = required_events(old_kind, new_kind)
        if required is None:
            raise IllegalTransition(f"{old_kind} → {new_kind} は遷移表に無い")
        if required and not any(event.kind in required for event in events):
            raise MissingEvent(f"{old_kind} → {new_kind} には {sorted(required)} のどれかが要る")


class _Definitions(_Base):
    """業務ルールの置き場"""

    def get(self, name: str) -> Definition | None:
        """読み出す — 名で1件"""
        row = self._con.execute("SELECT state FROM definitions WHERE id=?", (name,)).fetchone()
        return None if row is None else Definition.model_validate_json(row[0])

    def put(self, definition: Definition, events: Sequence[Event]) -> None:
        """書き込む — 業務ルールの門つき"""
        now = datetime.now(timezone.utc).isoformat()
        with self._write():
            self._require(
                definition_required_events(self.get(definition.name), definition),
                events,
                f"業務ルール {definition.name}",
            )
            self._con.execute(
                "INSERT INTO definitions(id, state, rev, updated_at) VALUES(?,?,1,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state, rev=rev+1, "
                "updated_at=excluded.updated_at",
                (definition.name, definition.model_dump_json(), now),
            )
            self._insert_events(events)

    def enacted(self) -> tuple[Definition, ...]:
        """有効なものたち — 有効な業務ルールの一覧"""
        rows = self._con.execute("SELECT state FROM definitions ORDER BY id").fetchall()
        loaded = (Definition.model_validate_json(row[0]) for row in rows)
        return tuple(d for d in loaded if d.enacted is not None)


class _Boards(_Base):
    """ボードの置き場"""

    def get(self, board_id: str) -> Board | None:
        """読み出す — id で1件"""
        row = self._con.execute("SELECT state FROM boards WHERE id=?", (board_id,)).fetchone()
        return None if row is None else Board.model_validate_json(row[0])

    def put(self, board: Board, events: Sequence[Event]) -> None:
        """書き込む — ボードの門つき"""
        now = datetime.now(timezone.utc).isoformat()
        with self._write():
            self._require(
                board_required_events(self.get(board.board_id), board),
                events,
                f"ボード {board.board_id}",
            )
            self._con.execute(
                "INSERT INTO boards(id, state, rev, updated_at) VALUES(?,?,1,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state, rev=rev+1, "
                "updated_at=excluded.updated_at",
                (board.board_id, board.model_dump_json(), now),
            )
            self._insert_events(events)


class _Participants(_Base):
    """参加者の置き場"""

    def get(self, participant_id: str) -> Participant | None:
        """読み出す — 参加者を1件読む"""
        row = self._con.execute(
            "SELECT state FROM participants WHERE id=?", (participant_id,)
        ).fetchone()
        return None if row is None else Participant.model_validate_json(row[0])

    def put(self, participant: Participant, events: Sequence[Event]) -> None:
        """書き込む — 登録と照合の結果を帳簿へ"""
        now = datetime.now(timezone.utc).isoformat()
        with self._write():
            self._con.execute(
                "INSERT INTO participants(id, state, rev, updated_at) VALUES(?,?,1,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state, rev=rev+1, "
                "updated_at=excluded.updated_at",
                (participant.participant_id, participant.model_dump_json(), now),
            )
            self._insert_events(events)


class _Artifacts(_Base):
    """成果物の置き場 — 積むだけ。置かれたら不変"""

    def append(self, artifact: Artifact) -> None:
        """積む — 成果物を帳簿に置く"""
        with self._write():
            self._con.execute(
                "INSERT INTO artifacts(at, kind, job_id, payload) VALUES(?,'Artifact',?,?)",
                (artifact.at.isoformat(), artifact.job_id, artifact.model_dump_json()),
            )

    def get(self, artifact_ref: str) -> Artifact | None:
        """読み出す — 参照で読む。同じ置き場に積まれていれば最後の1つ"""
        row = self._con.execute(
            "SELECT payload FROM artifacts WHERE json_extract(payload, '$.artifact_ref')=? "
            "ORDER BY seq DESC LIMIT 1",
            (artifact_ref,),
        ).fetchone()
        return None if row is None else Artifact.model_validate_json(row[0])


class _Evidences(_Base):
    """証拠の置き場 — 積むだけ。置かれたら不変"""

    def append(self, evidence: Evidence) -> None:
        """積む — 証拠を帳簿に置く"""
        with self._write():
            self._con.execute(
                "INSERT INTO evidences(at, kind, job_id, payload) VALUES(?,'Evidence',?,?)",
                (evidence.at.isoformat(), evidence.job_id, evidence.model_dump_json()),
            )

    def get(self, evidence_ref: str) -> Evidence | None:
        """読み出す — 参照で読む"""
        row = self._con.execute(
            "SELECT payload FROM evidences WHERE json_extract(payload, '$.evidence_ref')=? "
            "ORDER BY seq DESC LIMIT 1",
            (evidence_ref,),
        ).fetchone()
        return None if row is None else Evidence.model_validate_json(row[0])


class _Events(_Base):
    """出来事の置き場 — 積むだけの列"""

    def append(self, events: Sequence[Event]) -> None:
        """積む — 出来事を追記する"""
        with self._write():
            self._insert_events(events)

    def count(self, job_id: str, kind: str) -> int:
        """数える — その出来事が何度積まれたかを数える"""
        row = self._con.execute(
            "SELECT COUNT(*) FROM events WHERE job_id=? AND kind=?", (job_id, kind)
        ).fetchone()
        return int(row[0])


class SqliteLedger:
    """帳簿 — 集約ごとの置き場を差し出す場。1接続＝1スレッド"""

    def __init__(self, path: str | Path) -> None:
        # autocommit=True でトランザクションは自前で握る（書きは必ず BEGIN IMMEDIATE——
        # 読みから書きへ昇格するトランザクションは busy_timeout が効かない）
        self._con = sqlite3.connect(str(path), autocommit=True)
        self._con.execute("PRAGMA journal_mode=WAL;")
        self._con.execute("PRAGMA busy_timeout=5000;")
        self._con.execute("PRAGMA foreign_keys=ON;")
        self._con.executescript(_schema())
        self.jobs = _Jobs(self)
        self.definitions = _Definitions(self)
        self.boards = _Boards(self)
        self.participants = _Participants(self)
        self.artifacts = _Artifacts(self)
        self.events = _Events(self)
        self.evidences = _Evidences(self)

    @property
    def connection(self) -> sqlite3.Connection:
        """接続 — 置き場たちが分け合う1本"""
        return self._con

    @contextmanager
    def write(self) -> Iterator[None]:
        """書きトランザクション。最初から書きロックを取る（BEGIN IMMEDIATE）"""
        self._con.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._con.execute("ROLLBACK")
            raise
        else:
            self._con.execute("COMMIT")

    def insert_events(self, events: Sequence[Event]) -> None:
        """出来事を書き込みの中で積む（呼び出し側が書きトランザクションを握っている前提）"""
        for event in events:
            self._con.execute(
                "INSERT INTO events(at, kind, job_id, payload) VALUES(?,?,?,?)",
                (
                    event.at.isoformat(),
                    event.kind,
                    event.job_id,
                    event.model_dump_json(include={"payload"}),
                ),
            )

    # ---- 参照専用の読み（画面の材料。書かない） ----

    def standing_jobs(self) -> tuple[Job, ...]:
        """作成済みで、まだ完了していないタスクたち"""
        rows = self._con.execute(
            "SELECT state FROM jobs WHERE json_extract(state, '$.state.kind') "
            "NOT IN ('ClosedWithEvidence','ClosedBySelfReport') ORDER BY id"
        ).fetchall()
        return tuple(Job.model_validate_json(row[0]) for row in rows)

    def all_jobs(self) -> tuple[Job, ...]:
        """すべてのタスク — 完了も含めた帳簿の全タスク（検索が読む）。

        いまは全部読んでから絞る。件数が増えて遅いと**実測**できたら、
        絞り込みを SQL 側へ移す（消す前に測る・足す前に測る）。
        """
        rows = self._con.execute("SELECT state FROM jobs ORDER BY id").fetchall()
        return tuple(Job.model_validate_json(row[0]) for row in rows)

    def enacted_definitions(self) -> tuple[Definition, ...]:
        """有効な業務ルールたち（画面の予定が読む）"""
        return self.definitions.enacted()

    def events_for(self, job_id: str) -> tuple[Event, ...]:
        """1つのタスクの出来事を古い順に"""
        rows = self._con.execute(
            "SELECT at, kind, job_id, payload FROM events WHERE job_id=? ORDER BY seq", (job_id,)
        ).fetchall()
        return tuple(self._load_event(row) for row in rows)

    def recent_events(self, limit: int = 200) -> tuple[Event, ...]:
        """近ごろの出来事を新しい順に"""
        rows = self._con.execute(
            "SELECT at, kind, job_id, payload FROM events ORDER BY seq DESC LIMIT ?", (limit,)
        ).fetchall()
        return tuple(self._load_event(row) for row in rows)

    def origin_keys(self) -> frozenset[str]:
        """作成済みのタスクの作成元の鍵たち（画面が予定を導くのに使う）"""
        rows = self._con.execute(
            "SELECT origin_key FROM jobs WHERE origin_key IS NOT NULL"
        ).fetchall()
        return frozenset(str(row[0]) for row in rows)

    @staticmethod
    def _load_event(row: tuple[str, str, str | None, str]) -> Event:
        payload = json.loads(row[3]).get("payload", {})
        return Event(
            kind=row[1],  # type: ignore[arg-type]  # DB の値は EventKind のはず（読み込みで検証される）
            at=datetime.fromisoformat(row[0]),
            job_id=row[2],
            payload=payload,
        )
