"""窓の枠 — 画面を挟む白い器。

設計: 設計/人に見えるもの.md §1・どう作るか §5。

**脈を持たない。** 常駐は launchd のまま——窓を閉じても一座は回る
（長生きプロセスに脈を持たせる副作用は分析して捨てた）。
画面5枚（今日・予定・履歴・詳細・検索）は、これからこの枠に1枚ずつ挟む。
いまは真っ白——枠が先、中身は後。
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from ui.today import TodayScreen, 押す手, 詳細を読む手, 読む手


def make_window(
    fetch: 読む手 | None = None,
    act: 押す手 | None = None,
    detail: 詳細を読む手 | None = None,
) -> QMainWindow:
    """窓。読む手と押す手を注がれたら今日を挟む。無ければ真っ白のまま。"""
    window = QMainWindow()
    window.setWindowTitle("一座")
    window.resize(720, 560)
    if fetch is not None and act is not None:
        window.setCentralWidget(TodayScreen(fetch, act, detail))
    return window


def run(
    fetch: 読む手 | None = None,
    act: 押す手 | None = None,
    detail: 詳細を読む手 | None = None,
) -> int:
    app = QApplication(sys.argv)
    window = make_window(fetch, act, detail)
    window.show()
    return app.exec()
