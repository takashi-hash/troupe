"""源 — 腐敗防止層。外のファイルの言葉を、業務の語へ翻訳する。

設計: 設計/どう作るか.md §4。
| **adapters** | **業務の規則** | 帳簿の実装・Port の実装・**腐敗防止層** |
源の中身は**材料・引用・読めなかった理由**へ翻訳されてから中へ入る。

在りかの形は `file:相対パス` だけ。**`cmd:` や `http:` は後で足す**——
いまは読めなかった理由に倒す。読める形が増えたら、ここに実装を足す。

**読めたら常に引用（`Quote`）で返す。** 口には「何のために読むか」を渡す欄が無く、
呼ぶ側は材料でも引用でも本文を材料に使え（`consult` の1回目）、
根拠に積めるのは引用だけ（`consult` の取り直しと `confirm`）。
材料で返すと根拠が永久に積まれない——だからこの実装に `Material` の出口は無い。

例外は漏らさない。読めない理由は外の言葉（例外）ではなく、
中の語（読めなかった理由）になってから返る——**読めなければ `fail` へ**の材料。
"""

from __future__ import annotations

from pathlib import Path

from app.ports.source_port import Quote, SourceOutcome, Unreadable
from domain.value_objects.job.evidence import Evidence
from domain.value_objects.rule.source import Source

#: 読める在りかの形。この接頭辞に続く相対パスを根から読む。
FILE_PREFIX = "file:"


class FileSource:
    """源の実装 — 根からの相対パスでファイルを読む。出口は引用か、読めなかった理由。"""

    def __init__(self, root: Path = Path(".")) -> None:
        self._root = root

    def read(self, source: Source) -> SourceOutcome:
        """源から読む。読めたら引用、読めなければ理由。"""
        location = source.location
        if not location.startswith(FILE_PREFIX):
            return Unreadable(reason=f"読める在りかの形は file:相対パス だけです: {location}")
        path = self._root / location.removeprefix(FILE_PREFIX)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return Unreadable(reason=f"源のファイルが読めませんでした: {location}")
        except UnicodeDecodeError:
            return Unreadable(reason=f"源のファイルが文字として読めませんでした: {location}")
        if not text.strip():
            return Unreadable(reason=f"源のファイルが空でした: {location}")
        return Quote(evidence=Evidence(quote=text, source=source))


#: 診療録の在りかの形。`db:` に続く道が、診療録のどの抽出かを名指す。
EMR_PREFIX = "db:"

#: 事業所の「今日」。正本は診療録の口（adapters/emr）——同じ暦を2箇所で決めない。
from adapters.emr import TODAY  # noqa: E402


class EmrSource:
    """源の実装 — 事業所の診療録（EMR）から読む。**読むだけ。書く口は無い。**

    外の言葉（表と列）を、中の語（引用）へ翻訳する腐敗防止層。
    読めるのは名指しの抽出だけ——SQL が在りかに書けない（掟: 源は在りかであって問いではない）:

    - `db:chart/<患者記号>`   … カルテ抽出（患者・薬・指示書・次回訪問・直近の出来事・直近の記録）
    - `db:visit-schedule`     … 訪問予定（指示書の期限と状態変化を添えて）
    - `db:physician-orders`   … 指示書の台帳
    - `db:care-plans`         … 記録の鮮度と状態変化の一覧
    - `db:billing`            … 今月の会計抽出（算定・旗・未署名の実施済み・請求の下書き）

    繋がっていなければ「読めなかった理由」に倒す——**読めなければ `fail` へ**の材料。
    帳簿と同じ器（Cloud SQL）に住むが、**帳簿とは別の入れ物**——
    診療録は事業所の正本で、一座は客。引用して帳簿に積むだけ。
    """

    def __init__(self, dsn: str | None, connect: object | None = None) -> None:
        self._dsn = dsn
        self._connect = connect

    def read(self, source: Source) -> SourceOutcome:
        location = source.location
        道 = location.removeprefix(EMR_PREFIX)
        if self._dsn is None:
            return Unreadable(reason=f"診療録が繋がっていません（ICHIZA_EMR_DSN が空）: {location}")
        try:
            text = self._読む(道)
        except Exception as なぜ:  # 外の道具の例外は、外の言葉のまま漏らさない
            return Unreadable(reason=f"診療録が読めませんでした: {location}（{なぜ}）")
        if text is None:
            return Unreadable(reason=f"診療録にその在りかはありません: {location}")
        if not text.strip():
            return Unreadable(reason=f"診療録のその在りかは空でした: {location}")
        return Quote(evidence=Evidence(quote=text, source=source))

    def _開く(self) -> object:
        from adapters.emr import _connect

        assert self._dsn is not None  # read() が先に検めている
        return _connect(self._dsn, self._connect)

    def _読む(self, 道: str) -> str | None:
        conn = self._開く()
        try:
            if 道.startswith("chart/"):
                return _chart(conn, 道.removeprefix("chart/"))
            if 道 == "visit-schedule":
                return _visit_schedule(conn)
            if 道 == "physician-orders":
                return _orders(conn)
            if 道 == "care-plans":
                return _care_plans(conn)
            if 道 == "billing":
                return _billing(conn)
            return None
        finally:
            conn.close()  # type: ignore[attr-defined]


def _rows(conn: object, sql: str, args: tuple[object, ...] = ()) -> list[tuple[object, ...]]:
    return conn.execute(sql, args).fetchall()  # type: ignore[attr-defined]


def _chart(conn: object, code: str) -> str | None:
    """カルテ抽出 — 基本データと、**署名済みの記録だけ**を1枚の文へ。

    **下書き（note_drafts）は材料にならない。** 下書きが下書きを根拠にし始めると、
    提案と事実の区別が溶ける——読むのは clinical_notes（署名済み・不変）だけ。
    記録は**古い順に3件**——前回と前々回を比べられる並びで渡す。
    処方は**いま継続中のものだけ**（終了日の無いもの）。
    """
    patient = _rows(conn, "SELECT age, living_situation FROM patients WHERE code = %s", (code,))
    if not patient:
        return None
    age, living = patient[0]
    lines = [
        "# Patient chart (extract) - Riverbend Home Health (fictional agency)",
        "# NOTE: Entirely synthetic. Signed notes only - drafts are never source material.",
        "",
        f"Patient: {code}  ({age}, {living})",
    ]
    dx = _rows(
        conn,
        "SELECT dx, is_primary FROM patient_conditions WHERE patient = %s"
        " ORDER BY is_primary DESC, onset",
        (code,),
    )
    if dx:
        lines.append("Dx: " + " / ".join(f"{d}{' (primary)' if 主 else ''}" for d, 主 in dx))
    meds = _rows(
        conn,
        "SELECT drug, dose, frequency FROM medications"
        " WHERE patient = %s AND stopped IS NULL ORDER BY started",
        (code,),
    )
    if meds:
        lines.append("Current meds: " + " / ".join(f"{d} {dose} {f}" for d, dose, f in meds))
    for signed, expires, kind, practice in _rows(
        conn,
        "SELECT signed, expires, order_type, practice FROM physician_orders"
        " WHERE patient = %s ORDER BY expires DESC LIMIT 1",
        (code,),
    ):
        lines.append(f"Physician order: {kind} from {practice}, signed {signed}, expires {expires}")
    for 日, clinician, purpose in _rows(
        conn,
        "SELECT visit_date, clinician, purpose FROM visits"
        " WHERE patient = %s AND status = 'scheduled'"
        f" AND visit_date >= {TODAY} ORDER BY visit_date LIMIT 1",
        (code,),
    ):
        lines.append(f"Next visit: {日} ({clinician}) - {purpose}")
    events = _rows(
        conn,
        "SELECT event_date, description FROM condition_events"
        " WHERE patient = %s ORDER BY event_date DESC LIMIT 5",
        (code,),
    )
    if events:
        lines += ["", "Recent events:"]
        lines += [f"- {日}: {何} " for 日, 何 in events]
    記録 = _rows(
        conn,
        "SELECT note_date, clinician, s, o, a, p FROM clinical_notes"
        " WHERE patient = %s ORDER BY note_date DESC LIMIT 3",
        (code,),
    )
    for 日, clinician, s, o, a, p in reversed(記録):  # 古い順——傾向が読める並び
        lines += ["", f"Signed note ({日}, {clinician}):", f"S: {s}", f"O: {o}", f"A: {a}", f"P: {p}"]
    return "\n".join(lines)


def _visit_schedule(conn: object) -> str:
    """訪問予定 — 指示書の期限と直近の状態変化を、訪問の行に添えて。"""
    lines = [
        "# Visit schedule - Riverbend Home Health (fictional agency)  [from the agency EMR]",
        "# NOTE: Synthetic data. Columns: visit date / patient / clinician / purpose"
        " / physician order expires / condition change since last note",
        "",
    ]
    for 行 in _rows(
        conn,
        f"""
        SELECT v.visit_date, v.patient, v.clinician, v.purpose,
               (SELECT max(o.expires) FROM physician_orders o WHERE o.patient = v.patient),
               (SELECT e.event_date || ' ' || e.description FROM condition_events e
                 WHERE e.patient = v.patient
                   AND e.event_date > COALESCE((SELECT max(n.note_date) FROM clinical_notes n
                                                 WHERE n.patient = v.patient), DATE '1900-01-01')
                 ORDER BY e.event_date DESC LIMIT 1)
        FROM visits v
        WHERE v.status = 'scheduled' AND v.visit_date >= {TODAY} - 3
        ORDER BY v.visit_date, v.patient
        """,
    ):
        日, code, clinician, purpose, expires, change = 行
        lines.append(f"{日} / {code} / {clinician} / {purpose} / order expires {expires} / {change or 'none'}")
    穴 = _rows(
        conn,
        f"""
        SELECT p.patient, p.clinician, p.purpose
        FROM visit_patterns p
        WHERE p.active_from <= {TODAY}
          AND (p.active_to IS NULL OR p.active_to >= {TODAY})
          AND NOT EXISTS (
            SELECT 1 FROM visits v
            WHERE v.pattern_id = p.id AND v.status = 'scheduled'
              AND v.visit_date BETWEEN {TODAY} AND {TODAY} + 7
          )
        ORDER BY p.patient
        """,
    )
    if 穴:
        lines += ["", "# PATTERNS WITH NO VISIT SCHEDULED in the next 7 days"
                  " (the calendar has a hole - a human must fill it):"]
        lines += [f"{code} / {clinician} / {purpose}" for code, clinician, purpose in 穴]
    return "\n".join(lines)


def _orders(conn: object) -> str:
    lines = [
        "# Physician order register - Riverbend Home Health (fictional agency)  [from the agency EMR]",
        "# NOTE: Synthetic data. Columns: patient / practice / signed / expires / order type",
        "",
    ]
    for code, practice, signed, expires, kind in _rows(
        conn, "SELECT patient, practice, signed, expires, order_type FROM physician_orders ORDER BY patient"
    ):
        lines.append(f"{code} / {practice} / {signed} / {expires} / {kind}")
    return "\n".join(lines)


def _care_plans(conn: object) -> str:
    lines = [
        "# Note freshness and condition changes - Riverbend Home Health (fictional agency)  [from the agency EMR]",
        "# NOTE: Synthetic data. Columns: patient / last note written / latest condition change",
        "",
    ]
    for code, last, change in _rows(
        conn,
        """
        SELECT p.code,
               (SELECT max(n.note_date) FROM clinical_notes n WHERE n.patient = p.code),
               (SELECT e.event_date || ' ' || e.description FROM condition_events e
                 WHERE e.patient = p.code ORDER BY e.event_date DESC LIMIT 1)
        FROM patients p ORDER BY p.code
        """,
    ):
        lines.append(f"{code} / {last or 'never'} / {change or 'none'}")
    return "\n".join(lines)


class Sources:
    """源の口の束 — 在りかの形で実装を選ぶだけ。**翻訳はそれぞれの実装がする。**"""

    def __init__(self, file: FileSource, emr: EmrSource) -> None:
        self._file = file
        self._emr = emr

    def read(self, source: Source) -> SourceOutcome:
        if source.location.startswith(EMR_PREFIX):
            return self._emr.read(source)
        return self._file.read(source)


def _billing(conn: object) -> str | None:
    """会計抽出 — 今月の算定・旗・未署名の実施済み・請求の下書きを1枚の文へ。

    **読むだけ**。点数の計算は導出（機械）が済ませている——ここは AI が検算し、
    取りこぼしと旗を人に説明するための写し。週次と月次の両方の受け入れ基準が
    通るよう、月とISO週の両方の名札を持つ。**全部架空**（Nagisa Schedule）。
    """
    head = _rows(conn, """
        SELECT to_char((now() AT TIME ZONE 'Asia/Tokyo')::date, 'YYYY-MM'),
               to_char((now() AT TIME ZONE 'Asia/Tokyo')::date, 'IYYY-"W"IW')
    """)
    month, week = str(head[0][0]), str(head[0][1])
    lines = [
        "# Billing extract - Riverbend Home Medical Clinic (fictional)",
        "# Nagisa Schedule: every code, point value and payer here is INVENTED.",
        f"Month: {month}",
        f"ISO week: {week}",
        "",
        "## Claims (draft) this month",
    ]
    for pt, st, total, rate, copay in _rows(conn, """
        SELECT patient, status, total_points, copay_rate, copay_yen
        FROM claims WHERE month = %s ORDER BY patient""", (month,)):
        lines.append(f"- {pt}: {st}, {total} points, copay {copay} yen at {rate}0%")
    lines.append("")
    lines.append("## Flagged lines needing a human ruling")
    旗 = _rows(conn, """
        SELECT c.patient, c.day::text, c.code, f.name, c.flag_reason
        FROM charges c JOIN fee_schedule f ON f.code = c.code
        WHERE c.month = %s AND c.status = 'flagged' ORDER BY c.patient, c.day""", (month,))
    if 旗:
        for pt, day, code, name, reason in 旗:
            lines.append(f"- {pt} {day} {code} ({name}): {reason}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Completed visits with NO signed note (nothing derives until signed)")
    未署名 = _rows(conn, """
        SELECT v.patient, v.visit_date::text, v.clinician
        FROM visits v
        WHERE v.status = 'done' AND to_char(v.visit_date, 'YYYY-MM') = %s
          AND NOT EXISTS (SELECT 1 FROM clinical_notes n WHERE n.visit_id = v.id)
        ORDER BY v.visit_date, v.patient""", (month,))
    if 未署名:
        for pt, day, cl in 未署名:
            lines.append(f"- {pt} {day} ({cl}): done, unsigned - unbilled revenue at risk")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Visits under an expired physician order this month (billing risk)")
    期限切れ = _rows(conn, """
        SELECT DISTINCT v.patient, v.visit_date::text
        FROM visits v JOIN physician_orders o ON o.patient = v.patient
        WHERE v.status = 'done' AND to_char(v.visit_date, 'YYYY-MM') = %s
          AND v.visit_date > o.expires
          AND NOT EXISTS (SELECT 1 FROM physician_orders o2
                          WHERE o2.patient = v.patient AND o2.expires >= v.visit_date)
        ORDER BY v.patient, v.visit_date::text""", (month,))
    if 期限切れ:
        for pt, day in 期限切れ:
            lines.append(f"- {pt} {day}: visited after every order expired")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Same-building groups this month")
    for b, n in _rows(conn, """
        SELECT p.building, COUNT(DISTINCT c.patient) FROM charges c
        JOIN patients p ON p.code = c.patient
        WHERE c.month = %s AND p.building IS NOT NULL GROUP BY p.building""", (month,)):
        lines.append(f"- {b}: {n} managed patients (shared-building tier applies at 2+)")
    return "\n".join(lines)
