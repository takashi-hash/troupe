"""型レベルの禁止状態 — 「書くと pyright が落ちる」ことの見張り。

各行の `# type: ignore` は「ここで型エラーが出るべき」という宣言。
禁止が型で殺せなくなった瞬間、ignore が不要になり
reportUnnecessaryTypeIgnoreComment（pyproject で error）が赤にする。
実行はされない（pytest の対象外の名前）。
"""

from datetime import datetime

from domain.job import Core, IrreversibleApply, Lease, Ready


def _never_run() -> None:
    now = datetime(2026, 8, 21)

    # 禁止: 作業情報の無い未着手は書けない（Briefing が必須の材料）
    Ready()  # type: ignore

    # 禁止: 札を持つ未着手は書けない（Ready に Lease の欄が無い）
    Ready(lease=Lease(holder="機体-A", expires_at=now))  # type: ignore

    # 禁止: 承認待ちなしの不可逆反映は作れない（approval が必須の材料）
    IrreversibleApply(actor="機体-A", at=now)  # type: ignore

    # 禁止: 作成元の無いタスクは書けない（origin が Core の必須材料）
    Core(job_id="タスク-x", board_id="ボード/運転")  # type: ignore
