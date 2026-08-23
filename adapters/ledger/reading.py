"""帳簿からの読み — Reader の SQLite 実装（数と欄の正本は筋道 §4）。

設計: 設計/仕事が回る筋道.md §4「interface の正本」・§3。
**一覧の読みは集約を再構成しない**……が正本の言いかただが、ここは同じ帳簿を
読むので、要る欄だけを引く。**書く口は無い**——Reader は書かない。
"""

from __future__ import annotations

import json
from typing import Any

from adapters.ledger.db import Ledger
from adapters.ledger.jobs import load_job, read_events
from domain.aggregates.job.life import TERMINAL
from app.ports.detail_reader import DetailMaterial
from app.ports.history_reader import HistoryEntry
from app.ports.rule_reader import RuleLine
from app.ports.search_reader import SearchHit
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

    def __init__(self, conn: Ledger) -> None:
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

    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def keys(self) -> frozenset[str]:
        rows = self._conn.execute("SELECT origin FROM jobs").fetchall()
        return frozenset(str(r[0]) for r in rows)


class SqliteActiveRules:
    """`ActiveRuleReader` — 有効な版の（識別子・番号・周期）。"""

    def __init__(self, conn: Ledger) -> None:
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

    def __init__(self, conn: Ledger) -> None:
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


class SqliteDeliveredMarks:
    """`DeliveredMarkReader` — 既に「下書きが配達された」印の仕事。二度目を運ばない。"""

    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def marked_ids(self) -> frozenset[JobId]:
        rows = self._conn.execute(
            "SELECT DISTINCT job_id FROM job_events WHERE name = 'DraftDelivered'"
        ).fetchall()
        return frozenset(JobId(text=str(r[0])) for r in rows)


class SqliteOverdueMarks:
    """`OverdueMarkReader` — 既に「期日を過ぎた」の印が刻まれた仕事。二度目を刻まない。"""

    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def marked_ids(self) -> frozenset[JobId]:
        rows = self._conn.execute(
            "SELECT DISTINCT job_id FROM job_events WHERE name = 'DueDatePassed'"
        ).fetchall()
        return frozenset(JobId(text=str(r[0])) for r in rows)


class SqliteToday:
    """`TodayReader` — 今日の材料（仕様が見る domain の値）。終点は運ばない。"""

    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def read_all(self) -> tuple[TodayMaterial, ...]:
        out: list[TodayMaterial] = []
        # 終点の名は自分で数えない——正本は一生の TERMINAL（数える場所は正本を1つ）。
        # 出す・出さないの判定そのものは judge_today の仕事で、ここは読みの範囲だけ。
        置かない = ", ".join(f"'{name}'" for name in sorted(TERMINAL))
        for (id_text,) in self._conn.execute(
            f"SELECT id FROM jobs WHERE state_name NOT IN ({置かない}) ORDER BY id"
        ).fetchall():
            out.append(self._material(JobId(text=id_text)))
        return tuple(out)

    def read(self, id: JobId) -> TodayMaterial | None:
        """1件——終点も引ける（read_all だけが終点を運ばない）。"""
        row = self._conn.execute("SELECT 1 FROM jobs WHERE id = ?", (id.text,)).fetchone()
        return self._material(id) if row else None

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
            instruction=job.instruction,
            state_name=type(state).__name__,
            due=job.due,
            assignee_name=_assignee_name(state),
            recheck_at=recheck.at if recheck is not None else None,
            result_body=result_body,
            evidence_quote=evidence_quote,
            question_body=question_body,
            answer_body=answer_body,
            assessments=assessments,
            retried=job.retried,
            max_retries=job.max_retries,
            spent=job.spent,
            budget=job.budget,
            owner=job.owner,
        )


class SqliteDetail:
    """`DetailReader` — 出来事の列と問答の対だけ。成果・根拠・見立ては今日の材料が運ぶ。"""

    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def read(self, id: JobId) -> DetailMaterial:
        events: list[tuple[str, str, str | None, str]] = []
        for at, kind, name, ev_name in self._conn.execute(
            "SELECT at, by_kind, by_name, name FROM job_events WHERE job_id = ? ORDER BY seq",
            (id.text,),
        ).fetchall():
            events.append(
                (str(at)[:16].replace("T", " "), str(kind), str(name) if name else None, str(ev_name))
            )
        questions: list[tuple[str, str | None]] = []
        asked: list[str] = []
        for ev_name, body in read_events(self._conn, id):
            data = json.loads(body)
            if ev_name == "QuestionAsked":
                asked.append(str(data["body"]))
            elif ev_name == "QuestionAnswered" and asked:
                questions.append((asked.pop(0), str(data["body"])))
        questions.extend((q, None) for q in asked)
        return DetailMaterial(events=tuple(events), questions=tuple(questions))


class SqliteHistory:
    """`HistoryReader` — 出来事の列を新しい順に、どの仕事かの材料を添えて。"""

    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def read_latest(self, limit: int, offset: int = 0) -> tuple[HistoryEntry, ...]:
        out: list[HistoryEntry] = []
        for at, kind, name, ev_name, job_id, rule, period, body in self._conn.execute(
            "SELECT e.at, e.by_kind, e.by_name, e.name, e.job_id,"
            " j.rule_name, j.period, j.body"
            " FROM job_events e JOIN jobs j ON j.id = e.job_id"
            " ORDER BY e.at DESC, e.seq DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall():
            out.append(
                HistoryEntry(
                    at=str(at)[:16].replace("T", " "),
                    by_kind=str(kind),
                    by_name=str(name) if name else None,
                    name=str(ev_name),
                    job_id=str(job_id),
                    rule=str(rule) if rule else None,
                    period=str(period) if period else None,
                    instruction=json.loads(body)["instruction"]["text"],
                )
            )
        return tuple(out)

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM job_events").fetchone()
        return int(row[0]) if row else 0


class SqliteSearch:
    """`SearchReader` — 絞り込みの条件で仕事を引く。終わったものも含めて（F1）。

    キーワードは識別子・業務ルールの名・対象期間・帳簿の中身（やること等）に当てる。
    空の条件は絞らない。
    """

    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def read(
        self,
        keyword: str | None,
        state_name: str | None,
        rule: str | None,
        assignee: str | None,
    ) -> tuple[SearchHit, ...]:
        where: list[str] = []
        args: list[str] = []
        if keyword:
            where.append("(id LIKE ? OR rule_name LIKE ? OR period LIKE ? OR body LIKE ?)")
            args += [f"%{keyword}%"] * 4
        if state_name:
            where.append("state_name = ?")
            args.append(state_name)
        if rule:
            where.append("rule_name LIKE ?")
            args.append(f"%{rule}%")
        if assignee:
            where.append("assignee_name LIKE ?")
            args.append(f"%{assignee}%")
        条件 = f" WHERE {' AND '.join(where)}" if where else ""
        out: list[SearchHit] = []
        for id_text, rule_name, period, state, assignee_name, body in self._conn.execute(
            "SELECT id, rule_name, period, state_name, assignee_name, body"
            f" FROM jobs{条件} ORDER BY id",
            args,
        ).fetchall():
            job = json.loads(body)
            out.append(
                SearchHit(
                    id=str(id_text),
                    rule=str(rule_name) if rule_name else None,
                    period=str(period) if period else None,
                    instruction=job["instruction"]["text"],
                    state_name=str(state),
                    due=str(job["due"]["at"]),
                    assignee_name=str(assignee_name) if assignee_name else None,
                )
            )
        return tuple(out)


class SqliteRuleLines:
    """`RuleReader` — 業務ルールの一覧。やることは有効な版のもの、無ければ最新。"""

    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def read_all(self) -> tuple[RuleLine, ...]:
        out: list[RuleLine] = []
        for (body,) in self._conn.execute("SELECT body FROM rules ORDER BY name").fetchall():
            rule = json.loads(body)
            versions = rule["versions"]
            active = rule.get("active")
            picked = next(
                (v for v in versions if v["number"] == active), versions[-1]
            )
            out.append(
                RuleLine(
                    name=rule["name"]["text"],
                    version_number=int(versions[-1]["number"]),
                    active_version=int(active) if active is not None else None,
                    instruction=picked["instruction"]["text"],
                )
            )
        return tuple(out)
