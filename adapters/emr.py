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
from app.dto.patient_view import PatientDraft, PatientNote, PatientView

#: 事業所の「今日」。器（Cloud SQL）の時刻帯は UTC なので、暦の比べは事業所の時刻帯で開く。
TODAY = "(now() AT TIME ZONE 'Asia/Tokyo')::date"


def _connect(dsn: str, injected: Any) -> Any:
    """診療録への接続。**この1枚の3つの口が同じ開きかたを共有する。**"""
    if injected is not None:
        return injected(dsn)
    import psycopg

    return psycopg.connect(dsn, autocommit=True)


class PostgresPatients:
    """診療録の読み手 — Postgres の診療録から、画面に要る形で引く。"""

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def _開く(self) -> Any:
        assert self._dsn is not None
        return _connect(self._dsn, self._connect)

    def read_all(self) -> tuple[PatientRow, ...]:
        """患者の行の一覧。**繋がらなければ空**——参照は判断の材料で、無くても仕事は回る。"""
        if self._dsn is None:
            return ()
        try:
            conn = self._開く()
        except Exception:
            return ()  # 外の道具の例外は漏らさない——画面は空の状態を出す
        try:
            rows = conn.execute(
                f"""
                SELECT p.code, p.age, p.living_situation,
                       (SELECT c.dx FROM patient_conditions c
                         WHERE c.patient = p.code ORDER BY c.is_primary DESC, c.onset LIMIT 1),
                       (SELECT v.visit_date || ' (' || v.nurse || ')' FROM visits v
                         WHERE v.patient = p.code AND v.status = 'scheduled'
                           AND v.visit_date >= {TODAY}
                         ORDER BY v.visit_date LIMIT 1),
                       (SELECT max(o.expires)::text FROM physician_orders o
                         WHERE o.patient = p.code)
                FROM patients p ORDER BY p.code
                """
            ).fetchall()
        except Exception:
            return ()  # 読めない診療録は「空」——脈も画面も死なない
        finally:
            conn.close()
        return tuple(
            PatientRow(
                code=str(code), age=str(age), living=str(living),
                diagnosis=str(dx) if dx is not None else "—",
                next_visit=visit, order_expires=expires,
            )
            for code, age, living, dx, visit, expires in rows
        )

    def read_one(self, code: str) -> PatientView | None:
        if self._dsn is None:
            return None
        try:
            conn = self._開く()
        except Exception:
            return None  # 繋がらないのは「居ない」と同じ扱い——画面は静かに空を出す
        try:
            return self._読む(conn, code)
        except Exception:
            return None  # 読みのどの失敗も同じ——外の道具の例外は漏らさない
        finally:
            conn.close()

    def _読む(self, conn: Any, code: str) -> PatientView | None:
        """1人分を全部引いて組む。呼び手が接続の開け閉めと例外の境界を持つ。"""
        patient = conn.execute(
            "SELECT age, living_situation FROM patients WHERE code = %s",
            (code,),
        ).fetchall()
        if not patient:
            return None
        age, living = patient[0]
        条件 = conn.execute(
            "SELECT dx, is_primary FROM patient_conditions WHERE patient = %s"
            " ORDER BY is_primary DESC, onset",
            (code,),
        ).fetchall()
        dx = " / ".join(f"{d}{' (primary)' if 主 else ''}" for d, 主 in 条件) or "—"
        visit = conn.execute(
            "SELECT visit_date || ' (' || nurse || ') - ' || purpose FROM visits"
            " WHERE patient = %s AND status = 'scheduled'"
            " AND visit_date >= " + TODAY +
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
            " WHERE patient = %s AND stopped IS NULL ORDER BY started",
            (code,),
        ).fetchall()
        events = conn.execute(
            "SELECT event_date || ': ' || description FROM condition_events"
            " WHERE patient = %s ORDER BY event_date DESC",
            (code,),
        ).fetchall()
        drafts = conn.execute(
            "SELECT delivered_at::text, body, based_on_job FROM note_drafts"
            " WHERE patient = %s ORDER BY delivered_at DESC",
            (code,),
        ).fetchall()
        notes = conn.execute(
            "SELECT note_date, nurse, s, o, a, p, signed_at::text FROM clinical_notes"
            " WHERE patient = %s ORDER BY note_date DESC",
            (code,),
        ).fetchall()
        return PatientView(
            code=code, age=str(age), living=str(living), diagnosis=str(dx),
            next_visit=visit[0][0] if visit else None,
            order=order[0][0] if order else None,
            meds=tuple(m[0] for m in meds),
            events=tuple(e[0] for e in events),
            drafts=tuple(
                PatientDraft(delivered_at=str(at), body=str(b), job_id=str(j))
                for at, b, j in drafts
            ),
            notes=tuple(
                PatientNote(
                    at=str(at), nurse=str(n), s=str(s), o=str(o), a=str(a), p=str(pp),
                    signed_at=str(署名),
                )
                for at, n, s, o, a, pp, 署名 in notes
            ),
        )


class EmrDrafts:
    """下書き受け — `EmrDraftPort` の実装。**置けるのは draft だけ。**

    署名済み（clinical_notes）に触る SQL はこのクラスに1行も無い——
    書けない口であることが、読めば分かる形。
    冪等は診療録の一意の鍵（based_on_job UNIQUE）が決める。
    """

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def _開く(self) -> Any:
        assert self._dsn is not None
        return _connect(self._dsn, self._connect)

    def deposit(self, job_id: str, patient_code: str, body: str) -> bool:
        """受けに在る状態にできたら True。**届かなければ False**——次の脈がまた来る。

        既に在った（一意の鍵に弾かれた）も True——望んだ姿には既に成っている。
        例外は漏らさない: 診療録が落ちていても、時計の脈は死なない。
        """
        if self._dsn is None:
            return False  # 診療録が居ないなら、配達は静かに見送る
        try:
            conn = self._開く()
        except Exception:
            return False
        try:
            conn.execute(
                "INSERT INTO note_drafts(patient, body, based_on_job)"
                " VALUES (%s, %s, %s) ON CONFLICT (based_on_job) DO NOTHING",
                (patient_code, body, job_id),
            )
            return True
        except Exception:
            return False  # FK 違反（居ない患者）や一時故障——刻ませない
        finally:
            conn.close()
