"""仕立てのテスト — 例が仕様。集約境界図 §6 の表の1行が1つの確かめ。

新しい1件の形は**ドメインが決める**。2026-08-21 まで app が組んでいて、
期限の決め方（作成時刻＋版の日数）は設計のどこにも書かれていなかった。
"""

from datetime import datetime, timedelta, timezone

from domain.job import Budget, FromDefinition, Job, new_job

NOW = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
ORIGIN = FromDefinition(definition_name="週次の検査の見張り", version=1, period="2026-W34")
BUDGET = Budget(calls=20, seconds=600)


def made(days: int = 3) -> Job:
    return new_job(
        job_id="タスク-1", origin=ORIGIN, board_id="ボード/運転",
        now=NOW, deadline_days=days, budget=BUDGET,
    )


def test_deadline_is_now_plus_the_version_days() -> None:
    """期限は**作成した時刻 ＋ 版の日数**"""
    assert made(days=3).core.deadline == NOW + timedelta(days=3)
    assert made(days=1).core.deadline == NOW + timedelta(days=1)


def test_ready_at_is_now() -> None:
    """着手可能時刻は作成した時刻——予定を前倒ししない"""
    assert made().core.ready_at == NOW


def test_budget_is_a_copy_not_a_reference() -> None:
    """使用上限は版の写し——後から版が変わっても、このタスクは生まれた版の量で裁かれる"""
    assert made().core.budget == BUDGET


def test_a_new_job_starts_created() -> None:
    """初期状態は作成済み。作業情報はまだ無い（解決するのは配る輪）"""
    assert made().state.kind == "Created"


def test_the_id_is_received_not_minted() -> None:
    """採番は立てた者。仕立ては振られた ID を受け取るだけ"""
    assert made().core.job_id == "タスク-1"
