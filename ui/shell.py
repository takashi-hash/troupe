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


def make_window() -> QMainWindow:
    """白い窓。まだ何も知らない——帳簿も app も読まない。"""
    window = QMainWindow()
    window.setWindowTitle("一座")
    window.resize(720, 480)
    return window


def run() -> int:
    app = QApplication(sys.argv)
    window = make_window()
    window.show()
    return app.exec()
