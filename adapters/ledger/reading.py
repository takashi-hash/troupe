"""帳簿からの読み — Reader 5つの SQLite 実装。

設計: 設計/仕事が回る筋道.md §4「interface の正本」・§3。
**一覧の読みは集約を再構成しない**……が正本の言いかただが、ここは同じ帳簿を
読むので、要る欄だけを引く。**書く口は無い**——Reader は書かない。
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from adapters.ledger.jobs import load_job, read_events
from app.ports.work_reader import WorkMaterial
from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.today_material import TodayMaterial
from domain.value_objects.rule.rule_name import RuleName


def _assignee_name(state: object) -> str | None:
    """担当の名。受け持ちの人（`Owner`）は中の人の名。"""
    who = getattr(state, "assignee", None)
    person = getattr(who, "person", None)
    if person is not None:
        who = person
    name = getattr(who, "name", None)
    return str(name) if name is not None else None


class SqliteJobStates:
    """`JobStateReader` — ある状態の仕事の識別子。担当でも絞れる。"""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def ids_in(self, state_name: str, assignee_name: str | None = None) -> tuple[JobId, ...]:
        if assignee_name is None:
            rows = self._conn.execute(
                "SELECT id FROM jobs WHERE state_name = ? ORDER BY id", (state_name,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id FROM jobs WHERE state_name = ? AND assignee_name = ? ORDER BY id",
                (state_name, assignee_name),
            ).fetchall()
        return tuple(JobId(text=r[0]) for r in rows)


class SqliteOrigins:
    """`OriginReader` — 既にある仕事の作成元の鍵。"""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def keys(self) -> frozenset[str]:
        rows = self._conn.execute("SELECT origin FROM jobs").fetchall()
        return frozenset(str(r[0]) for r in rows)


class SqliteActiveRules:
    """`ActiveRuleReader` — 有効な版の（識別子・番号・周期）。"""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def read_all(self) -> tuple[tuple[RuleName, int, Cycle], ...]:
        out: list[tuple[RuleName, int, Cycle]] = []
        for (body,) in self._conn.execute("SELECT body FROM rules").fetchall():
            rule = json.loads(body)
            active = rule.get("active")
            if active is None:
                continue
            version = next(v for v in rule["versions"] if v["number"] == active)
            out.append(
                (RuleName(text=rule["name"]["text"]), int(active), Cycle(version["cycle"]))
            )
        return tuple(out)


class SqliteWork:
    """`WorkReader` — AI が1件こなすのに要る材料のうち、集約の外にあるもの。

    答えのある質問と落ちた理由は**出来事から**読む——出来事は消えない正本。
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def read(self, id: JobId) -> WorkMaterial:
        asked: list[str] = []
        answered: list[tuple[str, str]] = []
        falls: list[str] = []
        for name, body in read_events(self._conn, id):
            data = json.loads(body)
            if name == "QuestionAsked":
                asked.append(str(data["body"]))
            elif name == "QuestionAnswered" and asked:
                answered.append((asked.pop(0), str(data["body"])))
            elif name == "JobFailed":
                falls.append(str(data["fallen"]))
            elif name == "CheckStopped":
                falls.append(str(data["reason"]))
        row = self._conn.execute(
            "SELECT body, rule_name, period FROM jobs WHERE id = ?", (id.text,)
        ).fetchone()
        previous: str | None = None
        siblings: tuple[str, ...] = ()
        if row is not None:
            job = json.loads(row[0])
            at = job.get("result_at")
            if at:
                got = self._conn.execute(
                    "SELECT body FROM results WHERE at = ?", (at,)
                ).fetchone()
                previous = json.loads(got[0])["body"] if got else None
            if row[1] and row[2]:
                siblings = tuple(
                    str(r[0])
                    for r in self._conn.execute(
                        "SELECT state_name FROM jobs WHERE rule_name = ? AND period = ?"
                        " AND id != ?",
                        (row[1], row[2], id.text),
                    ).fetchall()
                )
        rows = self._conn.execute(
            "SELECT body FROM assessments WHERE job_id = ? ORDER BY at", (id.text,)
        ).fetchall()
        return WorkMaterial(
            answered_questions=tuple(answered),
            previous_result=previous,
            fall_reasons=tuple(falls),
            assessments=tuple(Assessment.model_validate_json(r[0]) for r in rows),
            sibling_states=siblings,
        )


class SqliteOverdueMarks:
    """`OverdueMarkReader` — 既に「期日を過ぎた」の印が刻まれた仕事。二度目を刻まない。"""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def marked_ids(self) -> frozenset[JobId]:
        rows = self._conn.execute(
            "SELECT DISTINCT job_id FROM job_events WHERE name = 'DueDatePassed'"
        ).fetchall()
        return frozenset(JobId(text=str(r[0])) for r in rows)


class SqliteToday:
    """`TodayReader` — 今日の材料（仕様が見る domain の値）。終点は運ばない。"""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def read_all(self) -> tuple[TodayMaterial, ...]:
        out: list[TodayMaterial] = []
        for (id_text,) in self._conn.execute(
            "SELECT id FROM jobs WHERE state_name NOT IN ('Finished', 'Abandoned')"
            " ORDER BY id"
        ).fetchall():
            out.append(self._material(JobId(text=id_text)))
        return tuple(out)

    def _material(self, id: JobId) -> TodayMaterial:
        body = self._conn.execute(
            "SELECT body FROM jobs WHERE id = ?", (id.text,)
        ).fetchone()[0]
        job = load_job(body)
        state: Any = job.state
        question_body: str | None = None
        answer_body: str | None = None
        request_head: str | None = None
        for name, ev in read_events(self._conn, id):
            data = json.loads(ev)
            if name == "QuestionAsked":
                question_body, answer_body = str(data["body"]), None
            elif name == "QuestionAnswered":
                answer_body = str(data["body"])
            elif name == "JobRequested":
                request_head = str(data["body"]).splitlines()[0]
        result_body: str | None = None
        if job.result_at:
            got = self._conn.execute(
                "SELECT body FROM results WHERE at = ?", (job.result_at,)
            ).fetchone()
            result_body = json.loads(got[0])["body"] if got else None
        evidence_quote: str | None = None
        if job.evidence_at:
            got = self._conn.execute(
                "SELECT body FROM evidence WHERE at = ?", (job.evidence_at,)
            ).fetchone()
            evidence_quote = json.loads(got[0])["quote"] if got else None
        assessments = tuple(
            Assessment.model_validate_json(r[0])
            for r in self._conn.execute(
                "SELECT body FROM assessments WHERE job_id = ? ORDER BY at", (id.text,)
            ).fetchall()
        )
        recheck = getattr(state, "recheck", None)
        return TodayMaterial(
            id=job.id,
            rule=job.born_of,
            born_version=job.born_version,
            period=job.period,
            request_head=request_head,
            state_name=type(state).__name__,
            due=job.due,
            assignee_name=_assignee_name(state),
            recheck_at=recheck.at if recheck is not None else None,
            result_body=result_body,
            evidence_quote=evidence_quote,
            question_body=question_body,
            answer_body=answer_body,
            assessments=assessments,
            retries_exhausted=job.retried >= job.max_retries,
            spent=job.spent,
            budget=job.budget,
            owner=job.owner,
        )
