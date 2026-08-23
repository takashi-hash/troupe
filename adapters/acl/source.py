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


class EmrSource:
    """源の実装 — 事業所の診療録（EMR）から読む。**読むだけ。書く口は無い。**

    外の言葉（表と列）を、中の語（引用）へ翻訳する腐敗防止層。
    読めるのは名指しの抽出だけ——SQL が在りかに書けない（掟: 源は在りかであって問いではない）:

    - `db:chart/<患者記号>`   … カルテ抽出（患者・薬・指示書・次回訪問・直近の出来事・直近の記録）
    - `db:visit-schedule`     … 訪問予定（指示書の期限と状態変化を添えて）
    - `db:physician-orders`   … 指示書の台帳
    - `db:care-plans`         … 記録の鮮度と状態変化の一覧

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
        assert self._dsn is not None  # read() が先に検めている
        if self._connect is not None:
            return self._connect(self._dsn)  # type: ignore[operator]
        import psycopg

        return psycopg.connect(self._dsn, autocommit=True)

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
            return None
        finally:
            conn.close()  # type: ignore[attr-defined]


def _rows(conn: object, sql: str, args: tuple[object, ...] = ()) -> list[tuple[object, ...]]:
    return conn.execute(sql, args).fetchall()  # type: ignore[attr-defined]


def _chart(conn: object, code: str) -> str | None:
    """カルテ抽出 — chart.txt と同じ形の文へ。**引用の単位は抽出1枚。**"""
    patient = _rows(conn, "SELECT age, living_situation, primary_dx FROM patients WHERE code = %s", (code,))
    if not patient:
        return None
    age, living, dx = patient[0]
    lines = [
        "# Patient chart (extract) - Riverbend Home Health (fictional agency)",
        "# NOTE: Entirely synthetic. Read from the agency EMR; Troupe never writes here.",
        "",
        f"Patient: {code}  ({age}, {living})",
        f"Primary dx: {dx}",
    ]
    meds = _rows(conn, "SELECT drug, dose, frequency FROM medications WHERE patient = %s", (code,))
    if meds:
        lines.append("Meds: " + " / ".join(f"{d} {dose} {f}" for d, dose, f in meds))
    for signed, expires, kind, practice in _rows(
        conn,
        "SELECT signed, expires, order_type, practice FROM physician_orders"
        " WHERE patient = %s ORDER BY expires DESC LIMIT 1",
        (code,),
    ):
        lines.append(f"Physician order: {kind} from {practice}, signed {signed}, expires {expires}")
    for 日, nurse, purpose in _rows(
        conn,
        "SELECT visit_date, nurse, purpose FROM visits"
        " WHERE patient = %s AND visit_date >= CURRENT_DATE ORDER BY visit_date LIMIT 1",
        (code,),
    ):
        lines.append(f"Next visit: {日} ({nurse}) - {purpose}")
    events = _rows(
        conn,
        "SELECT event_date, description FROM condition_events"
        " WHERE patient = %s ORDER BY event_date DESC LIMIT 5",
        (code,),
    )
    if events:
        lines += ["", "Recent events:"]
        lines += [f"- {日}: {何} " for 日, 何 in events]
    for 日, nurse, s, o, a, p in _rows(
        conn,
        "SELECT note_date, nurse, s, o, a, p FROM visit_notes"
        " WHERE patient = %s ORDER BY note_date DESC LIMIT 2",
        (code,),
    ):
        lines += ["", f"Visit note ({日}, {nurse}):", f"S: {s}", f"O: {o}", f"A: {a}", f"P: {p}"]
    return "\n".join(lines)


def _visit_schedule(conn: object) -> str:
    """訪問予定 — 指示書の期限と直近の状態変化を、訪問の行に添えて。"""
    lines = [
        "# Visit schedule - Riverbend Home Health (fictional agency)  [from the agency EMR]",
        "# NOTE: Synthetic data. Columns: visit date / patient / nurse / purpose"
        " / physician order expires / condition change since last note",
        "",
    ]
    for 行 in _rows(
        conn,
        """
        SELECT v.visit_date, v.patient, v.nurse, v.purpose,
               (SELECT max(o.expires) FROM physician_orders o WHERE o.patient = v.patient),
               (SELECT e.event_date || ' ' || e.description FROM condition_events e
                 WHERE e.patient = v.patient
                   AND e.event_date > COALESCE((SELECT max(n.note_date) FROM visit_notes n
                                                 WHERE n.patient = v.patient), DATE '1900-01-01')
                 ORDER BY e.event_date DESC LIMIT 1)
        FROM visits v
        WHERE v.visit_date >= CURRENT_DATE - 3
        ORDER BY v.visit_date, v.patient
        """,
    ):
        日, code, nurse, purpose, expires, change = 行
        lines.append(f"{日} / {code} / {nurse} / {purpose} / order expires {expires} / {change or 'none'}")
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
               (SELECT max(n.note_date) FROM visit_notes n WHERE n.patient = p.code),
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
