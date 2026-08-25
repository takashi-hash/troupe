"""積むだけの置き場2つ — 成果・根拠の SQLite 実装。

設計: 設計/仕事が回る筋道.md §4。**Store の積むは在りかを返す。**
積むだけ——書き換えの口が無い。質問・回答・見立てに置き場は無い——正本は出来事。

採番は器に言わせる（`RETURNING`）——「いま何件あるか」を先に数える書きかたは、
時計の脈と AI の鼓動が並んで書いた瞬間に同じ番号を2度振る。
"""

from __future__ import annotations


from adapters.ledger.db import Ledger
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.job.result import Result


def _番号(at: str) -> int | None:
    """`result://7` の尻の番号。読めなければ None——無い在りかは無い行。"""
    尻 = at.rsplit("//", 1)[-1]
    return int(尻) if 尻.isdigit() else None


class SqliteResults:
    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def put(self, result: Result) -> str:
        cur = self._conn.execute(
            "INSERT INTO results(body) VALUES (?) RETURNING at", (result.model_dump_json(),)
        )
        置いた = cur.fetchone()[0]
        self._conn.commit()
        return f"result://{置いた}"

    def get(self, at: str) -> Result | None:
        番号 = _番号(at)
        if 番号 is None:
            return None
        row = self._conn.execute("SELECT body FROM results WHERE at = ?", (番号,)).fetchone()
        return Result.model_validate_json(row[0]) if row else None


class SqliteEvidence:
    def __init__(self, conn: Ledger) -> None:
        self._conn = conn

    def put(self, evidence: Evidence) -> str:
        cur = self._conn.execute(
            "INSERT INTO evidence(body) VALUES (?) RETURNING at", (evidence.model_dump_json(),)
        )
        置いた = cur.fetchone()[0]
        self._conn.commit()
        return f"evidence://{置いた}"

    def get(self, at: str) -> Evidence | None:
        番号 = _番号(at)
        if 番号 is None:
            return None
        row = self._conn.execute("SELECT body FROM evidence WHERE at = ?", (番号,)).fetchone()
        return Evidence.model_validate_json(row[0]) if row else None
