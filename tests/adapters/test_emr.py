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
