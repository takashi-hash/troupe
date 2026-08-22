"""窓の枠の煙テスト。offscreen で開くだけ——CI でも回る。"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.shell import make_window


def test_白い窓が開いて題は一座() -> None:
    app = QApplication.instance() or QApplication([])
    window = make_window()
    assert window.windowTitle() == "一座"
    assert not window.centralWidget()  # まだ真っ白——中身は次の段
