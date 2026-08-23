"""診療録の読み手 — `PatientReader` の実装。**よそのコンテキストの写し。読むだけ。**

設計: 設計/どう作るか.md §5「診療録の読み手（emr）」・仕事が回る筋道.md §4。

診療録は事業所の正本（Cloud SQL の別の入れ物）。ここは表と列を、
画面が見る文字の入れ物（`PatientRow`・`PatientView`）へ写すだけ——
**中の語に翻訳しない**し、**書く口は無い**。

繋がっていなければ空を返す——参照は判断の材料であって、無くても仕事は回る
（源の読み `EmrSource` が別に居て、そちらは読めなければ fail の材料になる）。
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.dto.charge_row import ChargeRow
from app.dto.claim_view import ClaimView
from app.dto.fee_row import FeeRow
from app.dto.patient_row import PatientRow
from app.dto.staff_row import StaffRow
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
            "SELECT (delivered_at AT TIME ZONE 'Asia/Tokyo')::text, body, based_on_job,"
                " used_at IS NOT NULL FROM note_drafts"
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
                PatientDraft(delivered_at=str(at), body=str(b), job_id=str(j), used=bool(u))
                for at, b, j, u in drafts
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
        every_weeks: str = "1", *, by: str = "",
    ) -> str | None:
        if self._dsn is None:
            return "The EMR is not wired (ICHIZA_EMR_DSN is empty)"
        if weekday not in _WEEKDAYS:
            return f"Weekday must be one of {'/'.join(_WEEKDAYS)}"
        if not every_weeks.isdigit() or not 1 <= int(every_weeks) <= 12:
            return "Frequency must be between 1 and 12 weeks"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "Could not reach the EMR — try again in a moment"
        try:
            if _席の役(conn, by) is None:
                return "Only staff can record an agreement — this seat is not on the register"
            conn.execute(
                "INSERT INTO visit_patterns"
                "(patient, weekday, clinician, purpose, interval_weeks, active_from)"
                " VALUES (%s, %s, %s, %s, %s, %s::date)",
                (patient, _WEEKDAYS.index(weekday), clinician, purpose,
                 int(every_weeks), start),
            )
            return None
        except Exception as なぜ:
            return "Could not add — the patient (or clinician) is not in the EMR, or the date is malformed"
        finally:
            conn.close()

    def end(self, pattern_id: str, on: str, by: str) -> str | None:
        if self._dsn is None:
            return "The EMR is not wired (ICHIZA_EMR_DSN is empty)"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "Could not reach the EMR — try again in a moment"
        try:
            if _席の役(conn, by) is None:
                return "Only staff can end an agreement — this seat is not on the register"
            cur = conn.execute(
                "UPDATE visit_patterns SET active_to = %s::date"
                " WHERE id = %s::bigint AND active_to IS NULL",
                (on, pattern_id),
            )
            if not cur.rowcount:
                return "No such agreement (or it has already ended)"
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
            return "Could not end the agreement"
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



def _席の役(conn: Any, name: str) -> str | None:
    """登記簿の門——staff に居れば役を返し、居なければ None。力の源は名乗りではなく登記簿。"""
    rows = conn.execute("SELECT role FROM staff WHERE name = %s", (name,)).fetchall()
    return str(rows[0][0]) if rows else None


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
            return "The EMR is not wired (ICHIZA_EMR_DSN is empty)"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "Could not reach the EMR — try again in a moment"
        try:
            医師 = conn.execute(
                "SELECT 1 FROM clinicians WHERE code = %s AND active", (signer,)
            ).fetchall()
            if not 医師:
                return "Only a clinician's seat can sign — sit as Dr-A, Dr-B or Dr-C"
            with conn.transaction():
                done = conn.execute(
                    "UPDATE visits SET status = 'done'"
                    " WHERE id = %s::bigint AND status = 'scheduled'",
                    (visit_id,),
                )
                if not done.rowcount:
                    return "This visit is no longer scheduled (already done or cancelled)"
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
                        return "That draft has already been used — reload the page"
            return None
        except Exception as なぜ:
            名 = type(なぜ).__name__
            if "ForeignKey" in 名:
                return "The signer is not on the clinician roster"
            if "Unique" in 名:
                return "This visit already has a signed note"
            return "Could not sign — the EMR refused the record"
        finally:
            conn.close()

    def cancel(self, visit_id: str, reason: str, by: str) -> str | None:
        if self._dsn is None:
            return "The EMR is not wired (ICHIZA_EMR_DSN is empty)"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "Could not reach the EMR — try again in a moment"
        try:
            if _席の役(conn, by) is None:
                return "Only staff can cancel a visit — this seat is not on the register"
            cur = conn.execute(
                "UPDATE visits SET status = 'cancelled', cancelled_reason = %s"
                " WHERE id = %s::bigint AND status = 'scheduled'",
                (reason, visit_id),
            )
            return None if cur.rowcount else "This visit is no longer scheduled"
        except Exception:
            return "Could not cancel — the EMR refused"
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
        行為 = conn.execute(
            "SELECT vs.code, f.name, vs.qty FROM visit_services vs"
            " JOIN fee_schedule f ON f.code = vs.code"
            " WHERE vs.visit_id = %s::bigint ORDER BY vs.id",
            (visit_id,),
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
            services=tuple((str(c), str(n), int(q)) for c, n, q in 行為),
        )


# ========== 会計 — Nagisa Schedule(全部架空)。構造は本物を写し、数字は写さない ==========

#: 訪問料の類——週の上限と同日排他の対象。
_訪問料 = ("NV01", "NV02", "NO01")


def _薬剤点(yen: Decimal) -> int:
    """薬剤の円→点。**15円以下は1点、超えたら円/10を五捨五超入**(本物の型の写し)。

    五捨五超入: 端数がちょうど 0.5 なら捨て、0.5 を少しでも超えたら上げる。
    """
    if yen <= Decimal("15"):
        return 1
    十分の一 = yen / Decimal("10")
    底 = int(十分の一)
    return 底 + (1 if 十分の一 - 底 > Decimal("0.5") else 0)


def _材料点(yen: Decimal) -> int:
    """材料の円→点。円/10 を四捨五入(薬剤と丸めかたが違うのも本物の写し)。"""
    return int((yen / Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _行の点(kind: str, points: int | None, yen: Decimal | None, qty: int) -> int:
    if kind == "drug" and yen is not None:
        return _薬剤点(yen) * qty
    if kind == "material" and yen is not None:
        return _材料点(yen) * qty
    return int(points or 0) * qty


def _週の頭(d: date) -> date:
    """週の区切りは日曜はじまり(実務慣行の写し)。"""
    return d - timedelta(days=(d.weekday() + 1) % 7)


class PostgresFees:
    """点数表の読み — `FeeReader` の実装。読むだけ。"""

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def read_all(self) -> tuple[FeeRow, ...]:
        if self._dsn is None:
            return ()
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return ()
        try:
            rows = conn.execute(
                "SELECT code, name, kind, points, price_yen::text, unit, weekly_cap, note"
                " FROM fee_schedule ORDER BY code"
            ).fetchall()
            return tuple(
                FeeRow(
                    code=str(c), name=str(n), kind=str(k),
                    points=int(pt) if pt is not None else None,
                    price_yen=str(yen) if yen is not None else None,
                    unit=str(u), weekly_cap=int(w) if w is not None else None,
                    note=str(note),
                )
                for c, n, k, pt, yen, u, w, note in rows
            )
        except Exception:
            return ()
        finally:
            conn.close()


class EmrServices:
    """行為の口 — `EmrServicePort` の実装。**人の操作だけが呼ぶ。**

    署名前(status='scheduled')の訪問にだけ載る——署名で凍る。事実の門はひとつ。
    同じ行為をもう一度載せたら数量の上書き(記帳のし直し)。
    """

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def add(self, visit_id: str, code: str, qty: int, by: str) -> str | None:
        if self._dsn is None:
            return "The EMR is not wired (ICHIZA_EMR_DSN is empty)"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "Could not reach the EMR — try again in a moment"
        try:
            ok = conn.execute(
                "SELECT status FROM visits WHERE id = %s::bigint", (visit_id,)
            ).fetchall()
            if not ok:
                return "No such visit"
            if str(ok[0][0]) != "scheduled":
                return "The visit is already signed or cancelled — services are frozen"
            if not conn.execute(
                "SELECT 1 FROM clinicians WHERE code = %s AND active", (by,)
            ).fetchall():
                return "Only a clinician's seat records bedside services"
            種別 = conn.execute(
                "SELECT kind FROM fee_schedule WHERE code = %s", (code,)
            ).fetchall()
            if not 種別:
                return "That item is not on the fee schedule"
            if str(種別[0][0]) in ("visit", "oncall", "monthly"):
                return ("Visit fees and monthly tiers derive automatically — "
                        "only what was done at the bedside is entered here")
            conn.execute(
                "INSERT INTO visit_services(visit_id, code, qty, recorded_by)"
                " VALUES (%s::bigint, %s, %s, %s)"
                " ON CONFLICT (visit_id, code)"
                " DO UPDATE SET qty = EXCLUDED.qty, recorded_by = EXCLUDED.recorded_by",
                (visit_id, code, qty, by),
            )
            return None
        except Exception as なぜ:
            if "ForeignKey" in type(なぜ).__name__:
                return "That item is not on the fee schedule"
            return "Could not record the service — the EMR refused"
        finally:
            conn.close()

    def remove(self, visit_id: str, code: str, by: str) -> str | None:
        if self._dsn is None:
            return "The EMR is not wired (ICHIZA_EMR_DSN is empty)"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "Could not reach the EMR — try again in a moment"
        try:
            if not conn.execute(
                "SELECT 1 FROM clinicians WHERE code = %s AND active", (by,)
            ).fetchall():
                return "Only a clinician's seat records bedside services"
            ok = conn.execute(
                "SELECT status FROM visits WHERE id = %s::bigint", (visit_id,)
            ).fetchall()
            if not ok:
                return "No such visit"
            if str(ok[0][0]) != "scheduled":
                return "The visit is already signed or cancelled — services are frozen"
            cur = conn.execute(
                "DELETE FROM visit_services WHERE visit_id = %s::bigint AND code = %s",
                (visit_id, code),
            )
            return None if cur.rowcount else "That service is not on the visit"
        except Exception:
            return "Could not remove the service — the EMR refused"
        finally:
            conn.close()


class EmrCharges:
    """算定の導出 — `EmrChargePort` の実装。plan_visits の同型(展開は帳簿づけ)。

    読むのは**署名済みの訪問だけ**。点数の計算・回数の数えは判断ではない——
    上限に触れた行は**0点の旗**で置き、裁くのは人(`resolve_charge`)。
    人が触れた行(旗・裁き済み)は二度と機械が書き換えない。確定済みの月にも触れない。
    **このクラスに旗を裁く口も確定する口も無い。**
    """

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def derive(self) -> tuple[str, ...]:
        if self._dsn is None:
            return ()
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return ()
        try:
            made: list[str] = []
            master = {
                str(c): (str(k), int(pt) if pt is not None else None,
                         Decimal(str(yen)) if yen is not None else None,
                         str(u), int(w) if w is not None else None)
                for c, k, pt, yen, u, w in conn.execute(
                    "SELECT code, kind, points, price_yen, unit, weekly_cap FROM fee_schedule"
                ).fetchall()
            }
            # 窓は日付ではなく請求の状態——未確定の患者が1人でも居る月だけを導く
            months = [
                str(m[0]) for m in conn.execute(
                    "SELECT DISTINCT to_char(v.visit_date, 'YYYY-MM') FROM visits v"
                    " JOIN clinical_notes n ON n.visit_id = v.id"
                    " WHERE v.status = 'done'"
                    "   AND NOT EXISTS (SELECT 1 FROM claims cl WHERE cl.patient = v.patient"
                    "     AND cl.month = to_char(v.visit_date, 'YYYY-MM')"
                    "     AND cl.status = 'confirmed')"
                ).fetchall()
            ]
            for month in sorted(months):
                try:
                    with conn.transaction():
                        made += self._月を導く(conn, master, month)
                except Exception:
                    continue  # 1月の故障で他の月を道連れにしない(F7: 黙って全部止まるが最悪)
            return tuple(made)
        except Exception:
            return ()
        finally:
            conn.close()

    def _月を導く(self, conn: Any, master: dict, month: str) -> list[str]:
        made: list[str] = []
        # 署名済みの訪問(確定済みの月の患者は除く)
        rows = conn.execute(
            "SELECT v.id, v.patient, v.visit_date, v.kind, p.building, p.severe"
            " FROM visits v"
            " JOIN clinical_notes n ON n.visit_id = v.id"
            " JOIN patients p ON p.code = v.patient"
            " WHERE v.status = 'done' AND to_char(v.visit_date, 'YYYY-MM') = %s"
            "   AND NOT EXISTS (SELECT 1 FROM claims cl WHERE cl.patient = v.patient"
            "                    AND cl.month = %s AND cl.status = 'confirmed')"
            " ORDER BY v.patient, v.visit_date, v.id",
            (month, month),
        ).fetchall()
        visits = [
            (int(vid), str(pt), 日 if isinstance(日, date) else date.fromisoformat(str(日)),
             str(kind), str(b) if b is not None else None, bool(sv))
            for vid, pt, 日, kind, b, sv in rows
        ]
        # 同一建物×同日の患者数——**確定済みの隣人も数える**(書く先から外すだけで、判定からは外さない)
        建物日 = {}
        for b2, 日2, pt2 in conn.execute(
            "SELECT p.building, v.visit_date, v.patient FROM visits v"
            " JOIN clinical_notes n ON n.visit_id = v.id"
            " JOIN patients p ON p.code = v.patient"
            " WHERE v.status = 'done' AND v.kind = 'regular'"
            "   AND p.building IS NOT NULL"
            "   AND to_char(v.visit_date, 'YYYY-MM') = %s",
            (month,),
        ).fetchall():
            日2 = 日2 if isinstance(日2, date) else date.fromisoformat(str(日2))
            建物日.setdefault((str(b2), 日2), set()).add(str(pt2))
        # 同日の臨時(往診)を持つ患者×日
        臨時の日 = {(pt, 日) for _, pt, 日, kind, _, _ in visits if kind == "urgent"}
        # 週ごとの定期訪問料の数え(患者別・日付順)。**月の継ぎ目を跨いで数える**——
        # 隣の月に既に導出済みの同じ日曜週の行を初期値に足す(落とした行は数えない)
        週数: dict = {}
        for pt0, 日0 in conn.execute(
            "SELECT c.patient, c.day FROM charges c"
            " WHERE c.code = ANY(%s) AND c.status <> 'dropped' AND c.month <> %s"
            "   AND c.day BETWEEN (%s || '-01')::date - 6"
            "   AND ((%s || '-01')::date + INTERVAL '1 month' + INTERVAL '5 days')::date",
            (list(_訪問料), month, month, month),
        ).fetchall():
            日0 = 日0 if isinstance(日0, date) else date.fromisoformat(str(日0))
            鍵0 = (str(pt0), _週の頭(日0))
            週数[鍵0] = 週数.get(鍵0, 0) + 1
        for vid, pt, 日, kind, b, sv in visits:
            if kind == "urgent":
                code = "NO01"
                旗 = None
            else:
                code = "NV02" if (b and len(建物日.get((b, 日), ())) >= 2) else "NV01"
                鍵 = (pt, _週の頭(日))
                週数[鍵] = 週数.get(鍵, 0) + 1
                cap = master[code][4] or 99
                if 週数[鍵] > cap:
                    旗 = (f"Weekly visit-fee cap ({cap}) reached — visit {週数[鍵]} of the"
                          " week needs a ruling (exception with a reason, or drop)")
                elif (pt, 日) in 臨時の日:
                    旗 = ("An urgent call was charged the same day — the regular visit fee"
                          " needs a ruling (keep both with a reason, or drop)")
                else:
                    旗 = None
            点 = 0 if 旗 else _行の点(master[code][0], master[code][1], master[code][2], 1)
            # 既に別の訪問料が導出済みで、まだ機械の行なら、置き直す(同一建物の後着など)
            conn.execute(
                "DELETE FROM charges WHERE visit_id = %s::bigint AND status = 'derived'"
                " AND code = ANY(%s) AND code <> %s",
                (vid, list(_訪問料), code),
            )
            cur = conn.execute(
                "INSERT INTO charges(patient, month, day, visit_id, code, qty, points,"
                " status, flag_reason)"
                " VALUES (%s, %s, %s, %s, %s, 1, %s, %s, %s)"
                " ON CONFLICT (visit_id, code) DO UPDATE SET"
                "   points = EXCLUDED.points, status = EXCLUDED.status,"
                "   flag_reason = EXCLUDED.flag_reason"
                " WHERE charges.status = 'derived'"
                "   AND (charges.points IS DISTINCT FROM EXCLUDED.points"
                "     OR charges.status IS DISTINCT FROM EXCLUDED.status"
                "     OR charges.flag_reason IS DISTINCT FROM EXCLUDED.flag_reason)"
                " RETURNING id",
                (pt, month, 日, vid, code, 点,
                 "flagged" if 旗 else "derived", 旗),
            ).fetchall()
            if cur:
                made.append(f"{pt} {日} {code}")
            # 行為の行
            for scode, qty in conn.execute(
                "SELECT code, qty FROM visit_services WHERE visit_id = %s::bigint",
                (vid,),
            ).fetchall():
                scode, qty = str(scode), int(qty)
                kind2, pt2, yen2, unit2, _ = master[scode]
                旗2 = None
                if unit2 == "per_month":
                    dup = conn.execute(
                        "SELECT 1 FROM charges WHERE patient = %s AND month = %s"
                        " AND code = %s AND status <> 'dropped'"
                        " AND (visit_id IS NULL OR visit_id <> %s::bigint)",
                        (pt, month, scode, vid),
                    ).fetchall()
                    if dup:
                        旗2 = "Already charged this month (once-a-month item) — needs a ruling"
                elif unit2 == "per_quarter":
                    dup = conn.execute(
                        "SELECT 1 FROM charges WHERE patient = %s AND code = %s"
                        " AND status <> 'dropped'"
                        " AND (visit_id IS NULL OR visit_id <> %s::bigint)"
                        " AND to_date(month || '-01', 'YYYY-MM-DD')"
                        "     > to_date(%s || '-01', 'YYYY-MM-DD') - INTERVAL '3 months'"
                        " AND to_date(month || '-01', 'YYYY-MM-DD')"
                        "     <= to_date(%s || '-01', 'YYYY-MM-DD')",
                        (pt, scode, vid, month, month),
                    ).fetchall()
                    if dup:
                        旗2 = "Charged within the last 3 months (quarterly item) — needs a ruling"
                点2 = 0 if 旗2 else _行の点(kind2, pt2, yen2, qty)
                cur = conn.execute(
                    "INSERT INTO charges(patient, month, day, visit_id, code, qty, points,"
                    " status, flag_reason)"
                    " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    " ON CONFLICT (visit_id, code) DO UPDATE SET"
                    "   qty = EXCLUDED.qty, points = EXCLUDED.points,"
                    "   status = EXCLUDED.status, flag_reason = EXCLUDED.flag_reason"
                    " WHERE charges.status = 'derived'"
                    "   AND (charges.qty IS DISTINCT FROM EXCLUDED.qty"
                    "     OR charges.points IS DISTINCT FROM EXCLUDED.points"
                    "     OR charges.status IS DISTINCT FROM EXCLUDED.status"
                    "     OR charges.flag_reason IS DISTINCT FROM EXCLUDED.flag_reason)"
                    " RETURNING id",
                    (pt, month, 日, vid, scode, qty, 点2,
                     "flagged" if 旗2 else "derived", 旗2),
                ).fetchall()
                if cur:
                    made.append(f"{pt} {日} {scode}")
        # 月次の管理料(NC)——訪問料の数×重症×同一建物で区分。機械の行だけ置き直す
        counts = dict(conn.execute(
            "SELECT c.patient, COUNT(*) FROM charges c"
            " WHERE c.month = %s AND c.code = ANY(%s) AND c.status IN ('derived','allowed')"
            "   AND NOT EXISTS (SELECT 1 FROM claims cl WHERE cl.patient = c.patient"
            "     AND cl.month = %s AND cl.status = 'confirmed')"
            " GROUP BY c.patient",
            (month, list(_訪問料), month),
        ).fetchall())
        建物人数 = dict(conn.execute(
            "SELECT p.building, COUNT(DISTINCT c.patient) FROM charges c"
            " JOIN patients p ON p.code = c.patient"
            " WHERE c.month = %s AND p.building IS NOT NULL GROUP BY p.building",
            (month,),
        ).fetchall())
        重症 = {str(c): bool(s) for c, s in conn.execute(
            "SELECT code, severe FROM patients"
        ).fetchall()}
        建物 = {str(c): (str(b) if b is not None else None) for c, b in conn.execute(
            "SELECT code, building FROM patients"
        ).fetchall()}
        for pt, n in counts.items():
            pt, n = str(pt), int(n)
            if 重症.get(pt) and n >= 2:
                nc = "NC04"
            elif n >= 2 and 建物.get(pt) and int(建物人数.get(建物[pt], 0)) >= 2:
                nc = "NC02"
            elif n >= 2:
                nc = "NC01"
            else:
                nc = "NC03"
            conn.execute(
                "DELETE FROM charges WHERE patient = %s AND month = %s"
                " AND visit_id IS NULL AND code LIKE 'NC%%'"
                " AND status = 'derived' AND code <> %s",
                (pt, month, nc),
            )
            nc種, nc点, nc円, _, _ = master[nc]
            cur = conn.execute(
                "INSERT INTO charges(patient, month, day, visit_id, code, qty, points, status)"
                " SELECT %s, %s, (%s || '-01')::date, NULL, %s, 1, %s, 'derived'"
                " WHERE NOT EXISTS (SELECT 1 FROM charges WHERE patient = %s"
                "   AND month = %s AND visit_id IS NULL AND code = %s)"
                " RETURNING id",
                (pt, month, month, nc, _行の点(nc種, nc点, nc円, 1), pt, month, nc),
            ).fetchall()
            if cur:
                made.append(f"{pt} {month} {nc}")
        _請求を写す(conn, month)
        return made


def _請求を写す(conn: Any, month: str) -> None:
    """月次請求の下書きを算定行から写す(確定済みは触らない——トリガも守る)。"""
    conn.execute(
        "INSERT INTO claims(patient, month, status, total_points, copay_rate, copay_yen)"
        " SELECT c.patient, %s, 'draft', 0, p.copay_rate, 0"
        " FROM charges c JOIN patients p ON p.code = c.patient"
        " WHERE c.month = %s GROUP BY c.patient, p.copay_rate"
        " ON CONFLICT (patient, month) DO NOTHING",
        (month, month),
    )
    conn.execute(
        "UPDATE claims cl SET"
        " total_points = t.total,"
        " copay_yen = ((t.total * cl.copay_rate + 5) / 10) * 10"
        " FROM (SELECT patient, COALESCE(SUM(points), 0) AS total FROM charges"
        "       WHERE month = %s AND status IN ('derived','allowed')"
        "       GROUP BY patient) t"
        " WHERE cl.patient = t.patient AND cl.month = %s AND cl.status = 'draft'",
        (month, month),
    )


class EmrClaims:
    """旗の裁きと確定 — `EmrClaimPort` の実装。**人の操作だけが呼ぶ。**

    通す(allow)は点数を点数表から蘇らせ、理由は摘要の写しとして行に残る。
    確定は月が終わってから・旗が残っていれば断り。確定後の錠は DB のトリガ。
    """

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def resolve(self, charge_id: str, action: str, reason: str, by: str) -> str | None:
        if self._dsn is None:
            return "The EMR is not wired (ICHIZA_EMR_DSN is empty)"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "Could not reach the EMR — try again in a moment"
        try:
            with conn.transaction():
                if _席の役(conn, by) != "director":
                    return "Only the director's seat rules on a flagged line"
                row = conn.execute(
                    "SELECT c.code, c.qty, c.patient, c.month, f.kind, f.points, f.price_yen"
                    " FROM charges c JOIN fee_schedule f ON f.code = c.code"
                    " WHERE c.id = %s::bigint AND c.status = 'flagged'",
                    (charge_id,),
                ).fetchall()
                if not row:
                    return "That line is not waiting for a ruling"
                code, qty, patient, month, kind, pts, yen = row[0]
                点 = (_行の点(str(kind), int(pts) if pts is not None else None,
                             Decimal(str(yen)) if yen is not None else None, int(qty))
                      if action == "allow" else 0)
                conn.execute(
                    "UPDATE charges SET status = %s, points = %s,"
                    " resolve_reason = %s, resolved_by = %s"
                    " WHERE id = %s::bigint AND status = 'flagged'",
                    ("allowed" if action == "allow" else "dropped",
                     点, reason or None, by, charge_id),
                )
                _請求を写す(conn, str(month))
            return None
        except Exception:
            return "Could not rule on the line — the month may already be confirmed"
        finally:
            conn.close()

    def confirm(self, patient: str, month: str, by: str) -> str | None:
        if self._dsn is None:
            return "The EMR is not wired (ICHIZA_EMR_DSN is empty)"
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return "Could not reach the EMR — try again in a moment"
        try:
            with conn.transaction():
                if _席の役(conn, by) != "director":
                    return "Only the director's seat confirms a claim"
                conn.execute(
                    "SELECT 1 FROM claims WHERE patient = %s AND month = %s FOR UPDATE",
                    (patient, month),
                )
                今月 = str(conn.execute(
                    f"SELECT to_char({TODAY}, 'YYYY-MM')"
                ).fetchall()[0][0])
                if month >= 今月:
                    return "The month is not over yet — a claim is confirmed after month end"
                旗 = conn.execute(
                    "SELECT COUNT(*) FROM charges WHERE patient = %s AND month = %s"
                    " AND status = 'flagged'",
                    (patient, month),
                ).fetchall()
                if int(旗[0][0]):
                    return f"{int(旗[0][0])} flagged line(s) still need a ruling first"
                _請求を写す(conn, month)
                cur = conn.execute(
                    "UPDATE claims SET status = 'confirmed', confirmed_by = %s,"
                    " confirmed_at = now()"
                    " WHERE patient = %s AND month = %s AND status = 'draft'",
                    (by, patient, month),
                )
                if not cur.rowcount:
                    return "No draft claim for that patient and month (already confirmed?)"
            return None
        except Exception:
            return "Could not confirm — the EMR refused"
        finally:
            conn.close()


class PostgresBilling:
    """会計の読み — `BillingReader` の実装。読むだけ・文字とIDのまま。"""

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def read_month(self, month: str) -> tuple[ClaimView, ...]:
        if self._dsn is None:
            return ()
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return ()
        try:
            claims = conn.execute(
                "SELECT patient, status, total_points, copay_rate, copay_yen,"
                " confirmed_by, (confirmed_at AT TIME ZONE 'Asia/Tokyo')::text"
                " FROM claims WHERE month = %s ORDER BY patient",
                (month,),
            ).fetchall()
            lines = conn.execute(
                "SELECT c.id, c.patient, c.day::text, c.code, f.name, c.qty, c.points,"
                " c.status, c.flag_reason, c.resolve_reason, c.visit_id"
                " FROM charges c JOIN fee_schedule f ON f.code = c.code"
                " WHERE c.month = %s ORDER BY c.patient, c.day, c.id",
                (month,),
            ).fetchall()
            行 = {}
            for cid, pt, day, code, name, qty, points, st, fr, rr, vid in lines:
                行.setdefault(str(pt), []).append(ChargeRow(
                    id=str(cid), patient=str(pt), day=str(day), code=str(code),
                    name=str(name), qty=int(qty), points=int(points), status=str(st),
                    flag_reason=str(fr) if fr is not None else None,
                    resolve_reason=str(rr) if rr is not None else None,
                    visit_id=str(vid) if vid is not None else None,
                ))
            return tuple(
                ClaimView(
                    patient=str(pt), month=month, status=str(st),
                    total_points=int(total), copay_rate=int(rate), copay_yen=int(copay),
                    confirmed_by=str(cb) if cb is not None else None,
                    confirmed_at=str(ca)[:16] if ca is not None else None,
                    charges=tuple(行.get(str(pt), ())),
                )
                for pt, st, total, rate, copay, cb, ca in claims
            )
        except Exception:
            return ()
        finally:
            conn.close()

    def count_flagged(self) -> int:
        if self._dsn is None:
            return 0
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return 0
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM charges c WHERE c.status = 'flagged'"
                " AND NOT EXISTS (SELECT 1 FROM claims cl WHERE cl.patient = c.patient"
                "   AND cl.month = c.month AND cl.status = 'confirmed')"
            ).fetchall()
            return int(row[0][0]) if row else 0
        except Exception:
            return 0
        finally:
            conn.close()


class PostgresStaff:
    """職員の登記簿の読み — `StaffReader` の実装。読むだけ。"""

    def __init__(self, dsn: str | None, connect: Any = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def read_all(self) -> tuple[StaffRow, ...]:
        if self._dsn is None:
            return ()
        try:
            conn = _connect(self._dsn, self._connect)
        except Exception:
            return ()
        try:
            rows = conn.execute(
                "SELECT name, role FROM staff ORDER BY role, name"
            ).fetchall()
            return tuple(StaffRow(name=str(n), role=str(r)) for n, r in rows)
        except Exception:
            return ()
        finally:
            conn.close()
