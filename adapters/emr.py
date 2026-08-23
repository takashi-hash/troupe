"""診療録の読み手 — `PatientReader` の実装。**よそのコンテキストの写し。読むだけ。**

設計: 設計/どう作るか.md §5「診療録の読み手（emr）」・仕事が回る筋道.md §4。

診療録は事業所の正本（Cloud SQL の別の入れ物）。ここは表と列を、
画面が見る文字の入れ物（`PatientRow`・`PatientView`）へ写すだけ——
**中の語に翻訳しない**し、**書く口は無い**。

繋がっていなければ空を返す——参照は判断の材料であって、無くても仕事は回る
（源の読み `EmrSource` が別に居て、そちらは読めなければ fail の材料になる）。
"""

from __future__ import annotations

from typing import Any

from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientNote, PatientView


class PostgresPatients:
    """診療録の読み手 — Postgres の診療録から、画面に要る形で引く。"""

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def _開く(self) -> Any:
        assert self._dsn is not None
        if self._connect is not None:
            return self._connect(self._dsn)
        import psycopg

        return psycopg.connect(self._dsn, autocommit=True)

    def read_all(self) -> tuple[PatientRow, ...]:
        if self._dsn is None:
            return ()
        conn = self._開く()
        try:
            rows = conn.execute(
                """
                SELECT p.code, p.age, p.living_situation, p.primary_dx,
                       (SELECT v.visit_date || ' (' || v.nurse || ')' FROM visits v
                         WHERE v.patient = p.code AND v.visit_date >= CURRENT_DATE
                         ORDER BY v.visit_date LIMIT 1),
                       (SELECT max(o.expires)::text FROM physician_orders o
                         WHERE o.patient = p.code)
                FROM patients p ORDER BY p.code
                """
            ).fetchall()
        finally:
            conn.close()
        return tuple(
            PatientRow(
                code=str(code), age=str(age), living=str(living),
                diagnosis=str(dx), next_visit=visit, order_expires=expires,
            )
            for code, age, living, dx, visit, expires in rows
        )

    def read_one(self, code: str) -> PatientView | None:
        if self._dsn is None:
            return None
        conn = self._開く()
        try:
            patient = conn.execute(
                "SELECT age, living_situation, primary_dx FROM patients WHERE code = %s",
                (code,),
            ).fetchall()
            if not patient:
                return None
            age, living, dx = patient[0]
            visit = conn.execute(
                "SELECT visit_date || ' (' || nurse || ') - ' || purpose FROM visits"
                " WHERE patient = %s AND visit_date >= CURRENT_DATE"
                " ORDER BY visit_date LIMIT 1",
                (code,),
            ).fetchall()
            order = conn.execute(
                "SELECT order_type || ' from ' || practice || ', signed ' || signed"
                " || ', expires ' || expires FROM physician_orders"
                " WHERE patient = %s ORDER BY expires DESC LIMIT 1",
                (code,),
            ).fetchall()
            meds = conn.execute(
                "SELECT drug || ' ' || dose || ' ' || frequency FROM medications"
                " WHERE patient = %s",
                (code,),
            ).fetchall()
            events = conn.execute(
                "SELECT event_date || ': ' || description FROM condition_events"
                " WHERE patient = %s ORDER BY event_date DESC",
                (code,),
            ).fetchall()
            notes = conn.execute(
                "SELECT note_date, nurse, s, o, a, p FROM visit_notes"
                " WHERE patient = %s ORDER BY note_date DESC",
                (code,),
            ).fetchall()
        finally:
            conn.close()
        return PatientView(
            code=code, age=str(age), living=str(living), diagnosis=str(dx),
            next_visit=visit[0][0] if visit else None,
            order=order[0][0] if order else None,
            meds=tuple(m[0] for m in meds),
            events=tuple(e[0] for e in events),
            notes=tuple(
                PatientNote(at=str(at), nurse=str(n), s=str(s), o=str(o), a=str(a), p=str(pp))
                for at, n, s, o, a, pp in notes
            ),
        )
