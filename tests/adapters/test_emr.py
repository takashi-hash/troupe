"""診療録の口の壊しかた。設計/どう作るか §5——読み手と下書きの配達。

SQL は**実行して**確かめる——文字列の組み立ての傷は、実行しない試験を素通りする
（実際に素通りした）。本物の Postgres は在りかが渡ったときだけ（器は買うもの）。
落ちた診療録の畳み込み（空・None・偽）は接続の注入で常に見る。
"""

from __future__ import annotations

import os

import pytest

from adapters.emr import EmrDrafts, PostgresPatients


def _dsn() -> str:
    dsn = os.environ.get("ICHIZA_EMR_DSN")
    if not dsn:
        pytest.skip("ICHIZA_EMR_DSN が無いので、診療録は読まない")
    return dsn


def test_一覧のSQLが実行できて行になる() -> None:
    rows = PostgresPatients(_dsn()).read_all()
    assert rows, "種の入った診療録から1人も読めない"
    行 = rows[0]
    assert 行.code.startswith("P-")
    assert 行.diagnosis != "None"  # NULL の病名は — に倒す


def test_詳細のSQLが実行できて署名済みの記録が並ぶ() -> None:
    view = PostgresPatients(_dsn()).read_one("P-001")
    assert view is not None
    assert view.notes, "署名済みの記録が読めない"
    assert view.notes[0].signed_at  # 署名の時刻を必ず持つ


def test_居ない患者はNone() -> None:
    assert PostgresPatients(_dsn()).read_one("P-999") is None


# --- 落ちた診療録——例外は境界で倒れ、外へ漏れない ---

_落ちた口 = "postgresql://nobody@127.0.0.1:1/nope"


def test_落ちた診療録でも一覧は空に倒れる() -> None:
    assert PostgresPatients(_落ちた口).read_all() == ()


def test_落ちた診療録でも詳細はNoneに倒れる() -> None:
    assert PostgresPatients(_落ちた口).read_one("P-001") is None


def test_落ちた診療録でも配達は偽に倒れる() -> None:
    """脈は死なない——次の脈がまた来る。"""
    assert EmrDrafts(_落ちた口).deposit("J-1", "P-001", "draft") is False


def test_繋がっていない配達は偽() -> None:
    assert EmrDrafts(None).deposit("J-1", "P-001", "draft") is False


# --- 取り決め・予定づくり・道順——新しい口も**実行して**確かめる ---

from adapters.emr import PostgresPatterns, PostgresRoute, PostgresSchedule  # noqa: E402


def test_取り決めのSQLが実行できて行になる() -> None:
    rows = PostgresPatterns(_dsn()).read_all()
    assert rows and rows[0].weekday in ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")


def test_予定づくりは冪等で_地平はちょうど指定日数() -> None:
    """発端の傷（文字列の組み立て）をこの実行が塞ぐ。二度目はゼロ。"""
    import datetime

    dsn = _dsn()
    PostgresSchedule(dsn).plan(28)
    assert PostgresSchedule(dsn).plan(28) == ()  # 冪等
    # 地平の外（今日+28日目）はまだ無い——両端含みの1日ずれをここで留める
    先 = PostgresSchedule(dsn).plan(29)
    for 見出し in 先:
        日 = datetime.date.fromisoformat(見出し.split()[1])
        assert (日 - datetime.date.today()).days >= 28 - 1  # 29日目の週だけが増える


def test_道順のSQLが実行できて拠点と訪問が出る() -> None:
    from datetime import date, timedelta

    dsn = _dsn()
    PostgresSchedule(dsn).plan(28)
    # 次の月曜（P-001 の取り決めの曜日）
    今日 = date.today()
    月曜 = 今日 + timedelta(days=(0 - 今日.weekday()) % 7 or 7)
    base, visits = PostgresRoute(dsn).read_day(月曜.isoformat())
    assert base is not None and base.lat > 0
    assert any(v.patient == "P-001" for v in visits)


def test_取り決めを終えると由来の未来の予定が中止に倒れる() -> None:
    """レビューの1位——「解約したのに回り続ける」をここで留める。"""
    import psycopg

    dsn = _dsn()
    PostgresSchedule(dsn).plan(28)
    with psycopg.connect(dsn, autocommit=True) as conn:
        pid = conn.execute(
            "SELECT id FROM visit_patterns WHERE patient='P-006' AND active_to IS NULL LIMIT 1"
        ).fetchone()
        if pid is None:
            import pytest

            pytest.skip("P-006 の有効な取り決めが無い（別の試験が終えた後）")
        try:
            assert PostgresPatterns(dsn).end(str(pid[0]), "2026-08-24", "Director") is None
            残りの行 = conn.execute(
                "SELECT count(*) FROM visits WHERE pattern_id=%s AND status='scheduled'"
                " AND visit_date > '2026-08-24'", (pid[0],)
            ).fetchone()
            assert 残りの行 is not None and 残りの行[0] == 0  # 未来はぜんぶ中止
            実施の行 = conn.execute(
                "SELECT count(*) FROM visits WHERE pattern_id=%s AND status='done'", (pid[0],)
            ).fetchone()
            assert 実施の行 is not None and 実施の行[0] > 0  # 過去は触らない
        finally:
            # 後片づけは assert がどう転んでも走る——次の試験の場を汚さない
            conn.execute("UPDATE visit_patterns SET active_to=NULL WHERE id=%s", (pid[0],))
            conn.execute(
                "UPDATE visits SET status='scheduled' WHERE pattern_id=%s AND status='cancelled'",
                (pid[0],))


def test_訪問予定の抽出も穴のSQLも実行できる() -> None:
    from adapters.acl.source import EmrSource
    from domain.value_objects.rule.source import Source

    out = EmrSource(_dsn()).read(Source(location="db:visit-schedule"))
    assert out.kind == "quote"
    assert "clinician" in out.evidence.quote


# --- 署名——環を閉じる1トランザクションを、本物の診療録で ---

from adapters.emr import EmrVisits, PostgresVisit  # noqa: E402


def _次の予定の訪問(dsn: str) -> str:
    import psycopg

    with psycopg.connect(dsn) as conn:
        row = conn.execute(
            "SELECT id FROM visits WHERE status='scheduled' ORDER BY visit_date LIMIT 1"
        ).fetchone()
    if row is None:
        pytest.skip("予定の訪問が無い")
    return str(row[0])


def test_署名の一周_記録が積まれ訪問は実施済み_二度目は断り() -> None:
    """R1 の核心。署名 → 記録・done・（あれば）下書き使用済み、が1トランザクション。"""
    import psycopg

    dsn = _dsn()
    vid = _次の予定の訪問(dsn)
    view = PostgresVisit(dsn).read_one(vid)
    assert view is not None and view.status == "scheduled"
    draft = view.drafts[0].id if view.drafts else None

    assert EmrVisits(dsn).sign(vid, "Dr-A", "S text", "O text", "A text", "P text", draft) is None
    with psycopg.connect(dsn) as conn:
        try:
            状態行 = conn.execute("SELECT status FROM visits WHERE id=%s::bigint", (vid,)).fetchone()
            assert 状態行 is not None
            状態 = 状態行[0]
            記録 = conn.execute(
                "SELECT clinician, s FROM clinical_notes WHERE visit_id=%s::bigint", (vid,)
            ).fetchone()
            assert 状態 == "done" and 記録 == ("Dr-A", "S text")
            if draft:
                使用 = conn.execute(
                    "SELECT used_at IS NOT NULL, used_by_note IS NOT NULL"
                    " FROM note_drafts WHERE id=%s::bigint", (draft,)
                ).fetchone()
                assert 使用 == (True, True)
            # 二度目の署名は断り（実施済みには署名できない）
            assert EmrVisits(dsn).sign(vid, "Dr-A", "s", "o", "a", "p", None) is not None
            # 名簿に無い署名者も断り
            vid2 = conn.execute(
                "SELECT id FROM visits WHERE status='scheduled' ORDER BY visit_date LIMIT 1"
            ).fetchone()
            if vid2:
                assert EmrVisits(dsn).sign(str(vid2[0]), "Dr-Z", "s", "o", "a", "p", None) is not None
        finally:
            # 後片づけ: 署名した記録と done を種の姿へ戻す（トリガがあるので素の DELETE は不可）
            conn.execute("ALTER TABLE clinical_notes DISABLE TRIGGER clinical_notes_no_update")
            conn.execute("UPDATE note_drafts SET used_at=NULL, used_by_note=NULL WHERE used_by_note IN (SELECT id FROM clinical_notes WHERE visit_id=%s::bigint)", (vid,))
            conn.execute("DELETE FROM clinical_notes WHERE visit_id=%s::bigint", (vid,))
            conn.execute("ALTER TABLE clinical_notes ENABLE TRIGGER clinical_notes_no_update")
            conn.execute("UPDATE visits SET status='scheduled' WHERE id=%s::bigint", (vid,))
            conn.commit()


def test_単発の休みは理由つきで倒れ_取り決めは生きたまま() -> None:
    import psycopg

    dsn = _dsn()
    vid = _次の予定の訪問(dsn)
    assert EmrVisits(dsn).cancel(vid, "patient at a family event", "Director") is None
    with psycopg.connect(dsn) as conn:
        try:
            row = conn.execute(
                "SELECT status, cancelled_reason FROM visits WHERE id=%s::bigint", (vid,)
            ).fetchone()
            assert row == ("cancelled", "patient at a family event")
            # 実施済み・中止済みは休めない
            assert EmrVisits(dsn).cancel(vid, "again", "Director") is not None
        finally:
            conn.execute(
                "UPDATE visits SET status='scheduled', cancelled_reason=NULL WHERE id=%s::bigint",
                (vid,))
            conn.commit()


# --- 会計 — 点の換算は純関数(門なし)。実行系は自己整合で見る(状態に依存しない) ---


def test_薬剤の円から点は五捨五超入() -> None:
    """15円以下=1点。端数ちょうど0.5は捨て、超えたら上げ——四捨五入ではない。"""
    from decimal import Decimal

    from adapters.emr import _薬剤点

    assert _薬剤点(Decimal("9.80")) == 1     # 15円以下は1点
    assert _薬剤点(Decimal("15.00")) == 1
    assert _薬剤点(Decimal("15.10")) == 2    # 1.51 → 上げ
    assert _薬剤点(Decimal("104.00")) == 10  # 10.4 → 捨て
    assert _薬剤点(Decimal("105.00")) == 10  # 10.5 ちょうど → 捨て(五捨)
    assert _薬剤点(Decimal("105.10")) == 11  # 10.51 → 上げ(五超入)
    assert _薬剤点(Decimal("21.50")) == 2
    assert _薬剤点(Decimal("244.50")) == 24
    assert _薬剤点(Decimal("310.40")) == 31


def test_材料の円から点は四捨五入() -> None:
    """材料は円/10の四捨五入——薬剤と丸めかたが違うのも本物の写し。"""
    from decimal import Decimal

    from adapters.emr import _材料点

    assert _材料点(Decimal("120.00")) == 12
    assert _材料点(Decimal("115.00")) == 12  # 11.5 → 上げ(half-up)
    assert _材料点(Decimal("114.90")) == 11


def test_導出は何度回しても同じ() -> None:
    from adapters.emr import EmrCharges

    dsn = _dsn()
    EmrCharges(dsn).derive()
    assert EmrCharges(dsn).derive() == ()  # 2度目は何も生まれない


def _種の月(dsn: str) -> str:
    """試験の月は時計ではなくデータから導く——締切の朝に空にならないため。"""
    from adapters.emr import _connect

    conn = _connect(dsn, None)
    try:
        row = conn.execute(
            "SELECT max(to_char(v.visit_date, 'YYYY-MM')) FROM visits v"
            " JOIN clinical_notes n ON n.visit_id = v.id WHERE v.status = 'done'"
        ).fetchall()
        return str(row[0][0])
    finally:
        conn.close()


def test_導出は実りを生む() -> None:
    """壊れた導出が全試験を素通りしないための、実りの検（種の月に請求と行が立つ）。"""
    from adapters.emr import EmrCharges, PostgresBilling

    dsn = _dsn()
    EmrCharges(dsn).derive()
    views = PostgresBilling(dsn).read_month(_種の月(dsn))
    assert views, "種の月に請求が1枚も立たない"
    assert any(v.charges for v in views), "算定行が1本も無い"
    # 凍った種から独立に検算できる1点: P-003 の ND02 は 21.50円×7 → 2点×7 = 14
    p3 = next((v for v in views if v.patient == "P-003"), None)
    if p3 is not None and p3.status == "draft":
        nd02 = [c for c in p3.charges if c.code == "ND02"]
        if nd02:
            assert nd02[0].points == 14


def test_確定の錠は生きている() -> None:
    """掟7: 壊して赤を見る——確定済みの月の行は UPDATE も DELETE も DB が拒む。"""
    from adapters.emr import _connect

    conn = _connect(_dsn(), None)
    try:
        row = conn.execute(
            "SELECT c.id FROM charges c JOIN claims cl"
            " ON cl.patient = c.patient AND cl.month = c.month"
            " WHERE cl.status = 'confirmed' LIMIT 1"
        ).fetchall()
        if not row:
            pytest.skip("確定済みの月が無い(白紙の帳簿)")
        try:
            conn.execute("UPDATE charges SET points = points + 1 WHERE id = %s", (row[0][0],))
        except Exception as なぜ:
            assert "confirmed" in str(なぜ) or "locked" in str(なぜ)
        else:
            raise AssertionError("確定済みの行が書き換えられてしまった——錠が死んでいる")
    finally:
        conn.close()


def test_裁きの往復で点が蘇り合計が動く() -> None:
    """旗を allow で裁くと点数表から点が蘇り、請求の合計も動く。終わったら旗に戻す。"""
    from adapters.emr import EmrCharges, EmrClaims, PostgresBilling, _connect

    dsn = _dsn()
    EmrCharges(dsn).derive()
    month = _種の月(dsn)
    views = {v.patient: v for v in PostgresBilling(dsn).read_month(month)}
    旗 = next(
        (c for v in views.values() if v.status == "draft"
         for c in v.charges if c.status == "flagged" and c.code == "NV01"),
        None,
    )
    if 旗 is None:
        pytest.skip("旗の行が無い(既に裁かれた帳簿)")
    前 = views[旗.patient].total_points
    assert EmrClaims(dsn).resolve(旗.id, "allow", "test exception ruling", "Director") is None
    try:
        後 = {v.patient: v for v in PostgresBilling(dsn).read_month(month)}[旗.patient]
        通った = next(c for c in 後.charges if c.id == 旗.id)
        assert 通った.status == "allowed" and 通った.points == 800
        assert 後.total_points == 前 + 800
    finally:
        conn = _connect(dsn, None)
        try:
            conn.execute(
                "UPDATE charges SET status = 'flagged', points = 0,"
                " resolve_reason = NULL, resolved_by = NULL WHERE id = %s",
                (旗.id,),
            )
        finally:
            conn.close()
        EmrCharges(dsn).derive()  # 合計を写し直す


def test_請求の合計は算定行の和と一致する() -> None:
    """下書き請求の総点数 = 数えられる行(導出+通った)の和。負担金は点×割を10円丸め。"""
    from adapters.emr import EmrCharges, PostgresBilling

    dsn = _dsn()
    EmrCharges(dsn).derive()
    month = _種の月(dsn)
    for view in PostgresBilling(dsn).read_month(month):
        if view.status != "draft":
            continue
        和 = sum(c.points for c in view.charges if c.status in ("derived", "allowed"))
        assert view.total_points == 和, f"{view.patient}: {view.total_points} != {和}"
        assert view.copay_yen == ((view.total_points * view.copay_rate + 5) // 10) * 10


def test_旗の行は0点で理由を持つ() -> None:
    from adapters.emr import EmrCharges, PostgresBilling

    dsn = _dsn()
    EmrCharges(dsn).derive()
    month = _種の月(dsn)
    for view in PostgresBilling(dsn).read_month(month):
        for c in view.charges:
            if c.status == "flagged":
                assert c.points == 0 and c.flag_reason


def test_確定は月が終わるまで断られる() -> None:
    from adapters.emr import EmrClaims

    month = __import__("datetime").date.today().strftime("%Y-%m")
    なぜ = EmrClaims(_dsn()).confirm("P-001", month, "Director")
    assert なぜ is not None and "not over" in なぜ


def test_裁きは旗の行にだけ() -> None:
    from adapters.emr import EmrClaims

    なぜ = EmrClaims(_dsn()).resolve("999999", "drop", "", "Director")
    assert なぜ is not None and "not waiting" in なぜ
