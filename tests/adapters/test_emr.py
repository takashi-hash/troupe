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
            assert PostgresPatterns(dsn).end(str(pid[0]), "2026-08-24") is None
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
