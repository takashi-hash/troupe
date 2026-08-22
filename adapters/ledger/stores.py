"""積むだけの置き場4つ — 成果・根拠・質問と回答・見立ての SQLite 実装。

設計: 設計/仕事が回る筋道.md §4。**Store の積むは在りかを返す。**
積むだけ——書き換えの口が無い。
"""

from __future__ import annotations


from adapters.ledger.db import Ledger
from domain.value_objects.job.answer import Answer
from domain.value_objects.job.assessment import Assessment
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.job.job_id import JobId
from domain.value_objects.job.question import Question
from domain.value_objects.job.result import Result


class SqliteResults:
    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def put(self, result: Result) -> str:
        cur = self._conn.execute("SELECT COUNT(*) FROM results").fetchone()
        at = f"result://{int(cur[0]) + 1}"
        self._conn.execute(
            "INSERT INTO results(at, body) VALUES (?, ?)", (at, result.model_dump_json())
        )
        self._conn.commit()
        return at

    def get(self, at: str) -> Result | None:
        row = self._conn.execute("SELECT body FROM results WHERE at = ?", (at,)).fetchone()
        return Result.model_validate_json(row[0]) if row else None


class SqliteEvidence:
    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def put(self, evidence: Evidence) -> str:
        cur = self._conn.execute("SELECT COUNT(*) FROM evidence").fetchone()
        at = f"evidence://{int(cur[0]) + 1}"
        self._conn.execute(
            "INSERT INTO evidence(at, body) VALUES (?, ?)", (at, evidence.model_dump_json())
        )
        self._conn.commit()
        return at

    def get(self, at: str) -> Evidence | None:
        row = self._conn.execute("SELECT body FROM evidence WHERE at = ?", (at,)).fetchone()
        return Evidence.model_validate_json(row[0]) if row else None


class SqliteQuestions:
    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def put_question(self, q: Question) -> str:
        cur = self._conn.execute("SELECT COUNT(*) FROM questions").fetchone()
        at = f"question://{int(cur[0]) + 1}"
        self._conn.execute(
            "INSERT INTO questions(at, question) VALUES (?, ?)", (at, q.model_dump_json())
        )
        self._conn.commit()
        return at

    def put_answer(self, question_at: str, a: Answer) -> None:
        done = self._conn.execute(
            "UPDATE questions SET answer = ? WHERE at = ? AND answer IS NULL",
            (a.model_dump_json(), question_at),
        )
        if done.rowcount != 1:
            raise ValueError("その質問はありません（または答え済みです）")
        self._conn.commit()

    def get(self, at: str) -> tuple[Question, Answer | None] | None:
        row = self._conn.execute(
            "SELECT question, answer FROM questions WHERE at = ?", (at,)
        ).fetchone()
        if row is None:
            return None
        q = Question.model_validate_json(row[0])
        a = Answer.model_validate_json(row[1]) if row[1] else None
        return q, a


class SqliteAssessments:
    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def put(self, job: JobId, a: Assessment) -> str:
        # 採番は器に言わせる（`RETURNING`）——「いま入れた行の番号」を
        # あとから尋ねる書きかたは器ごとに違い、手元でしか通らない
        cur = self._conn.execute(
            "INSERT INTO assessments(job_id, body) VALUES (?, ?) RETURNING at",
            (job.text, a.model_dump_json()),
        )
        置いた = cur.fetchone()[0]
        self._conn.commit()
        return f"assessment://{置いた}"

    def list_for(self, job: JobId) -> tuple[Assessment, ...]:
        rows = self._conn.execute(
            "SELECT body FROM assessments WHERE job_id = ? ORDER BY at", (job.text,)
        ).fetchall()
        return tuple(Assessment.model_validate_json(r[0]) for r in rows)
