"""帳簿が黙って壊れないことのテスト（段C）。

**古い帳簿は捨ててよい**——注入し直せばボードと業務ルールは戻る。
だめなのは黙って壊れること。気づくのが古い帳簿を開いた日になり、
そのとき何が起きたのか分からない。だから大きな声で止める。
"""

import pytest

from adapters.sqlite_ledger import SCHEMA_VERSION, SqliteLedger, StaleLedger


def test_a_fresh_ledger_stamps_its_shape(tmp_path) -> None:
    """新しい帳簿は、自分の形の番号を刻む"""
    ledger = SqliteLedger(str(tmp_path / "a.db"))
    row = ledger.connection.execute("SELECT version FROM schema_version").fetchone()
    assert int(row[0]) == SCHEMA_VERSION


def test_a_ledger_of_another_shape_refuses_to_open(tmp_path) -> None:
    """形の番号が違う帳簿は開かない——読めないと名乗って止まる"""
    path = str(tmp_path / "b.db")
    first = SqliteLedger(path)
    first.connection.execute("PRAGMA writable_schema=ON")  # 番号は積むだけなので直に書き換える
    first.connection.execute("UPDATE schema_version SET version=?", (SCHEMA_VERSION + 1,))
    first.connection.close()
    with pytest.raises(StaleLedger) as caught:
        SqliteLedger(path)
    assert "入れ直す" in str(caught.value)


def test_a_row_that_does_not_fit_the_type_names_itself(tmp_path) -> None:
    """いまの型で読めない行は、名乗って止まる（pydantic の生の悲鳴を外に出さない）"""
    ledger = SqliteLedger(str(tmp_path / "c.db"))
    ledger.connection.execute(
        "INSERT INTO jobs(id, state, rev, updated_at) VALUES(?,?,1,?)",
        ("タスク-古", '{"core": {"job_id": "タスク-古"}, "state": {"kind": "Created"}}', "2026-08-21"),
    )
    with pytest.raises(StaleLedger) as caught:
        ledger.jobs.get("タスク-古")
    assert "入れ直す" in str(caught.value)
