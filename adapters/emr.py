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
from app.dto.pattern_row import PatternRow
from app.dto.visit_view import UnusedDraft, VisitView
from app.ports.route_reader import RouteBase, RouteVisit

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
                       (SELECT v.visit_date || ' (' || v.clinician || ')' FROM visits v
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
            "SELECT visit_date || ' (' || clinician || ') - ' || purpose FROM visits"
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
            "SELECT (delivered_at AT TIME ZONE 'Asia/Tokyo')::text, body, based_on_job FROM note_drafts"
            " WHERE patient = %s ORDER BY delivered_at DESC",
            (code,),
        ).fetchall()
        notes = conn.execute(
            "SELECT note_date, clinician, s, o, a, p, signed_at::text FROM clinical_notes"
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
                    at=str(at), clinician=str(n), s=str(s), o=str(o), a=str(a), p=str(pp),
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


#: 曜日の橋。診療録は 0=日〜6=土、画面は名で見る。
_WEEKDAYS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")


class PostgresPatterns:
    """取り決めの口 — `EmrPatternPort` の実装。人の操作だけが呼ぶ。"""

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def read_all(self) -> tuple[PatternRow, ...]:
        if self._dsn is None:
            return ()
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return ()
        try:
            rows = conn.execute(
                "SELECT id, patient, weekday, clinician, purpose, interval_weeks,"
                " active_from::text, active_to::text"
                " FROM visit_patterns ORDER BY patient, weekday"
            ).fetchall()
        except Exception:
            return ()
        finally:
            conn.close()
        return tuple(
            PatternRow(
                id=str(id), patient=str(pt), weekday=_WEEKDAYS[int(wd)],
                every_weeks=str(ew), clinician=str(cl), purpose=str(pu),
                active_from=str(af), active_to=at,
            )
            for id, pt, wd, cl, pu, ew, af, at in rows
        )

    def add(
        self, patient: str, weekday: str, clinician: str, purpose: str, start: str,
        every_weeks: str = "1",
    ) -> str | None:
        if self._dsn is None:
            return "診療録が繋がっていません"
        if weekday not in _WEEKDAYS:
            return f"曜日は {'/'.join(_WEEKDAYS)} のどれかです"
        if not every_weeks.isdigit() or not 1 <= int(every_weeks) <= 12:
            return "週の間隔は 1〜12 です"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "診療録に届きませんでした"
        try:
            conn.execute(
                "INSERT INTO visit_patterns"
                "(patient, weekday, clinician, purpose, interval_weeks, active_from)"
                " VALUES (%s, %s, %s, %s, %s, %s::date)",
                (patient, _WEEKDAYS.index(weekday), clinician, purpose,
                 int(every_weeks), start),
            )
            return None
        except Exception as なぜ:
            return "載せられませんでした——その患者が診療録に居ないか、日付の形が違います"
        finally:
            conn.close()

    def end(self, pattern_id: str, on: str) -> str | None:
        if self._dsn is None:
            return "診療録が繋がっていません"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "診療録に届きませんでした"
        try:
            cur = conn.execute(
                "UPDATE visit_patterns SET active_to = %s::date"
                " WHERE id = %s::bigint AND active_to IS NULL",
                (on, pattern_id),
            )
            if not cur.rowcount:
                return "その取り決めはありません（または終わっています）"
            # 判断の帳簿づけの巻き戻し——この取り決め由来で、まだ来ていない予定は中止に倒す。
            # 実施済み（done）と臨時（pattern_id なし）には触らない。
            conn.execute(
                "UPDATE visits SET status = 'cancelled'"
                " WHERE pattern_id = %s::bigint AND status = 'scheduled'"
                "   AND visit_date > %s::date",
                (pattern_id, on),
            )
            return None
        except Exception:
            return "終えられませんでした"
        finally:
            conn.close()


class PostgresSchedule:
    """予定づくりの口 — `EmrSchedulePort` の実装。**取り決め由来の予定だけを作る。**

    1つの INSERT が読み（有効な取り決め×日付）と書きを兼ねる——
    一意の鍵（取り決め×日付）に既にあれば何もしない（冪等）。
    臨時（pattern_id が空）・中止・署名済みに触る SQL はここに1行も無い。
    """

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def plan(self, days_ahead: int) -> tuple[str, ...]:
        if self._dsn is None:
            return ()
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return ()  # 届かなければ空——次の脈がまた来る
        try:
            rows = conn.execute(
                f"""
                INSERT INTO visits(pattern_id, visit_date, patient, clinician, purpose)
                SELECT p.id, d::date, p.patient, p.clinician, p.purpose
                FROM visit_patterns p,
                     generate_series({TODAY}, {TODAY} + (%s - 1), INTERVAL '1 day') d
                WHERE EXTRACT(dow FROM d) = p.weekday
                  AND d::date >= p.active_from
                  AND (p.active_to IS NULL OR d::date <= p.active_to)
                  AND (((d::date - p.active_from) / 7) %% p.interval_weeks) = 0
                ON CONFLICT (pattern_id, visit_date) DO NOTHING
                RETURNING patient, visit_date::text
                """,
                (days_ahead,),
            ).fetchall()
        except Exception:
            return ()
        finally:
            conn.close()
        return tuple(f"{pt} {d}" for pt, d in rows)


class PostgresRoute:
    """道順の材料の読み — `RouteReader` の実装。その日の予定と拠点、**下書きの支度つき**。

    支度は診療録だけから導く: 署名済みの記録が既に在れば「signed」、
    未使用の下書きが在れば「draft」、どちらも無ければ「none」。
    """

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def read_day(self, day: str) -> tuple[RouteBase | None, tuple[RouteVisit, ...]]:
        if self._dsn is None:
            return None, ()
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return None, ()
        try:
            base = conn.execute("SELECT name, lat, lng FROM clinic LIMIT 1").fetchall()
            rows = conn.execute(
                """
                SELECT v.id, v.patient, v.clinician, v.purpose, p.address, p.lat, p.lng,
                       CASE
                         WHEN EXISTS (SELECT 1 FROM clinical_notes n WHERE n.visit_id = v.id)
                           THEN 'signed'
                         WHEN EXISTS (SELECT 1 FROM note_drafts d
                                       WHERE d.patient = v.patient AND d.used_at IS NULL)
                           THEN 'draft'
                         ELSE 'none'
                       END
                     , v.status
                FROM visits v JOIN patients p ON p.code = v.patient
                WHERE v.visit_date = %s::date
                ORDER BY v.patient
                """,
                (day,),
            ).fetchall()
        except Exception:
            return None, ()
        finally:
            conn.close()
        拠点 = RouteBase(name=str(base[0][0]), lat=float(base[0][1]), lng=float(base[0][2])) if base else None
        return 拠点, tuple(
            RouteVisit(visit_id=str(vid), patient=str(pt), clinician=str(cl),
                       purpose=str(pu), place=str(ad), lat=float(la), lng=float(ln),
                       prep=str(prep), status=str(st))
            for vid, pt, cl, pu, ad, la, ln, prep, st in rows
        )


class EmrVisits:
    """訪問の終わり — `EmrVisitPort` の実装。**人の操作だけが呼ぶ。**

    署名は1トランザクション: 記録を積む・訪問を実施済みへ・下書きに使用の印。
    守りは診療録の側に3層——status='scheduled' のガード付き UPDATE、
    1訪問1記録の一意鍵、署名済みの不変トリガ。**書き換える口はこのクラスに無い。**
    """

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def sign(
        self, visit_id: str, signer: str,
        s: str, o: str, a: str, p: str, draft_id: str | None,
    ) -> str | None:
        if self._dsn is None:
            return "診療録が繋がっていません"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "診療録に届きませんでした"
        try:
            with conn.transaction():
                done = conn.execute(
                    "UPDATE visits SET status = 'done'"
                    " WHERE id = %s::bigint AND status = 'scheduled'",
                    (visit_id,),
                )
                if not done.rowcount:
                    return "その訪問は予定のままではありません（実施済みか中止済み）"
                row = conn.execute(
                    "INSERT INTO clinical_notes"
                    "(patient, visit_id, note_date, clinician, s, o, a, p, signed_at)"
                    " SELECT v.patient, v.id, v.visit_date, %s, %s, %s, %s, %s, now()"
                    " FROM visits v WHERE v.id = %s::bigint"
                    " RETURNING id",
                    (signer, s, o, a, p, visit_id),
                ).fetchone()
                if draft_id:
                    used = conn.execute(
                        "UPDATE note_drafts SET used_at = now(), used_by_note = %s"
                        " WHERE id = %s::bigint AND used_at IS NULL",
                        (row[0], draft_id),
                    )
                    if not used.rowcount:
                        return "その下書きは既に使われています——読み直してください"
            return None
        except Exception as なぜ:
            名 = type(なぜ).__name__
            if "ForeignKey" in 名:
                return "署名者が名簿にありません"
            if "Unique" in 名:
                return "この訪問には既に署名済みの記録があります"
            return "署名できませんでした——診療録が受けませんでした"
        finally:
            conn.close()

    def cancel(self, visit_id: str, reason: str) -> str | None:
        if self._dsn is None:
            return "診療録が繋がっていません"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "診療録に届きませんでした"
        try:
            cur = conn.execute(
                "UPDATE visits SET status = 'cancelled', cancelled_reason = %s"
                " WHERE id = %s::bigint AND status = 'scheduled'",
                (reason, visit_id),
            )
            return None if cur.rowcount else "その訪問は予定のままではありません"
        except Exception:
            return "休めませんでした——診療録が受けませんでした"
        finally:
            conn.close()


class PostgresVisit:
    """訪問の読み — `VisitReader` の実装。当日入力の材料ぜんぶを1回で。"""

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def read_one(self, visit_id: str) -> VisitView | None:
        if self._dsn is None:
            return None
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return None
        try:
            return self._読む(conn, visit_id)
        except Exception:
            return None
        finally:
            conn.close()

    def _読む(self, conn: Any, visit_id: str) -> VisitView | None:
        v = conn.execute(
            f"""
            SELECT v.id, v.visit_date::text, v.clinician, v.purpose, v.status,
                   p.code, p.age, p.living_situation, p.address,
                   (SELECT c.dx FROM patient_conditions c
                     WHERE c.patient = p.code ORDER BY c.is_primary DESC, c.onset LIMIT 1),
                   (SELECT max(o.expires)::text FROM physician_orders o
                     WHERE o.patient = p.code)
            FROM visits v JOIN patients p ON p.code = v.patient
            WHERE v.id = %s::bigint
            """,
            (visit_id,),
        ).fetchall()
        if not v:
            return None
        vid, 日, 担当, 目的, 状態, code, age, living, addr, dx, expires = v[0]
        drafts = conn.execute(
            "SELECT id, body, (delivered_at AT TIME ZONE 'Asia/Tokyo')::text"
            " FROM note_drafts WHERE patient = %s AND used_at IS NULL"
            " ORDER BY delivered_at DESC",
            (code,),
        ).fetchall()
        notes = conn.execute(
            "SELECT note_date, clinician, s, o, a, p, signed_at::text FROM clinical_notes"
            " WHERE patient = %s ORDER BY note_date DESC LIMIT 5",
            (code,),
        ).fetchall()
        名簿 = conn.execute(
            "SELECT code FROM clinicians WHERE active ORDER BY code"
        ).fetchall()
        return VisitView(
            id=str(vid), visit_date=str(日), clinician=str(担当), purpose=str(目的),
            status=str(状態),
            patient=PatientRow(
                code=str(code), age=str(age), living=str(living),
                diagnosis=str(dx) if dx is not None else "—",
                next_visit=None, order_expires=expires,
            ),
            drafts=tuple(
                UnusedDraft(id=str(i), body=str(b), delivered_at=str(at)[:16])
                for i, b, at in drafts
            ),
            notes=tuple(
                PatientNote(at=str(at), clinician=str(cl), s=str(ss), o=str(oo),
                            a=str(aa), p=str(pp), signed_at=str(sg))
                for at, cl, ss, oo, aa, pp, sg in notes
            ),
            clinicians=tuple(str(c[0]) for c in 名簿),
        )
