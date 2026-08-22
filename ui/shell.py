"""窓の枠 — 画面を挟む白い器。

設計: 設計/人に見えるもの.md §1・どう作るか §5。

**脈を持たない。** 常駐は launchd のまま——窓を閉じても一座は回る
（長生きプロセスに脈を持たせる副作用は分析して捨てた）。
挟まっているのは今日・予定・履歴・検索（詳細は一覧の行から開く）。
**押しつけは今日だけ**——残りは引き出し（タブ）。
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from ui.history import HistoryScreen, FetchHistory
from ui.schedule import ScheduleScreen, FetchSchedule, PressRule
from ui.search import SearchScreen, SearchJobs
from ui.today import TodayScreen, Press, FetchDetail, FetchToday


def make_window(
    fetch: FetchToday | None = None,
    act: Press | None = None,
    detail: FetchDetail | None = None,
    schedule_fetch: FetchSchedule | None = None,
    schedule_act: PressRule | None = None,
    history_fetch: FetchHistory | None = None,
    search: SearchJobs | None = None,
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
    if history_fetch is not None:
        tabs.addTab(HistoryScreen(history_fetch, act, detail), "履歴")
    if search is not None:
        tabs.addTab(SearchScreen(search, act, detail), "検索")
    if tabs.count():
        window.setCentralWidget(tabs)
    return window


def run(
    fetch: FetchToday | None = None,
    act: Press | None = None,
    detail: FetchDetail | None = None,
    schedule_fetch: FetchSchedule | None = None,
    schedule_act: PressRule | None = None,
    history_fetch: FetchHistory | None = None,
    search: SearchJobs | None = None,
) -> int:
    app = QApplication(sys.argv)
    window = make_window(fetch, act, detail, schedule_fetch, schedule_act, history_fetch, search)
    window.show()
    return app.exec()
