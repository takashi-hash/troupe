"""窓の枠 — 画面を挟む白い器。

設計: 設計/人に見えるもの.md §1・どう作るか §5。

**脈を持たない。** 常駐は launchd のまま——窓を閉じても一座は回る
（長生きプロセスに脈を持たせる副作用は分析して捨てた）。
挟まっているのは今日と予定（詳細は一覧の行から開く）。履歴・検索はこれから。
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from ui.schedule import ScheduleScreen, 予定を読む手, 決まりを押す手
from ui.today import TodayScreen, 押す手, 詳細を読む手, 読む手


def make_window(
    fetch: 読む手 | None = None,
    act: 押す手 | None = None,
    detail: 詳細を読む手 | None = None,
    schedule_fetch: 予定を読む手 | None = None,
    schedule_act: 決まりを押す手 | None = None,
) -> QMainWindow:
    """窓。注がれた手のぶんだけ画面を挟む——押しつけは今日だけ、残りは引き出し（タブ）。"""
    window = QMainWindow()
    window.setWindowTitle("一座")
    window.resize(760, 600)
    tabs = QTabWidget()
    if fetch is not None and act is not None:
        tabs.addTab(TodayScreen(fetch, act, detail), "今日")
    if schedule_fetch is not None and schedule_act is not None:
        tabs.addTab(ScheduleScreen(schedule_fetch, schedule_act), "予定")
    if tabs.count():
        window.setCentralWidget(tabs)
    return window


def run(
    fetch: 読む手 | None = None,
    act: 押す手 | None = None,
    detail: 詳細を読む手 | None = None,
    schedule_fetch: 予定を読む手 | None = None,
    schedule_act: 決まりを押す手 | None = None,
) -> int:
    app = QApplication(sys.argv)
    window = make_window(fetch, act, detail, schedule_fetch, schedule_act)
    window.show()
    return app.exec()
