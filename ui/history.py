"""履歴 — 過去に何を頼み、何が済んだ？

設計: 設計/人に見えるもの.md §1「履歴」。
**引き出しの画面**（押しつけは今日だけ）。出来事の列が新しい順に、
どの仕事かの見出しつきで見える（F4）。行から詳細が開く。
入っているものを出すだけ——判定も詰め替えもしない。
"""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.dto.history_row import HistoryRow
from ui.today import 押す手, 詳細を読む手


class 履歴を読む手(Protocol):
    def __call__(self) -> tuple[HistoryRow, ...]: ...


class HistoryScreen(QWidget):
    """履歴の画面。読む手を注がれて並べるだけ。行の詳細は今日と同じ小窓で開く。"""

    def __init__(
        self,
        fetch: 履歴を読む手,
        act: 押す手 | None = None,
        detail: 詳細を読む手 | None = None,
    ) -> None:
        super().__init__()
        self._fetch = fetch
        self._act = act
        self._detail = detail
        self._word = QLabel()
        self._word.setWordWrap(True)
        self._rows_box = QVBoxLayout()
        self._rows_box.setAlignment(Qt.AlignmentFlag.AlignTop)

        host = QWidget()
        host.setLayout(self._rows_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(host)

        更新 = QPushButton("更新")
        更新.clicked.connect(self.refresh)

        outer = QVBoxLayout()
        outer.addWidget(更新)
        outer.addWidget(self._word)
        outer.addWidget(scroll)
        self.setLayout(outer)
        self.refresh()

    def refresh(self) -> None:
        while self._rows_box.count():
            item = self._rows_box.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        rows = self._fetch()
        if not rows:
            self._word.setText("履歴はまだありません")
            return
        self._word.setText(f"出来事: {len(rows)}件（新しい順）")
        for row in rows:
            self._rows_box.addWidget(self._line(row))

    def _line(self, row: HistoryRow) -> QWidget:
        line = QWidget()
        box = QHBoxLayout()
        box.setContentsMargins(0, 0, 0, 0)
        label = QLabel(f"{row.at}　{row.by}　{row.what}　— {row.head}")
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(label, stretch=1)
        if self._detail is not None and self._act is not None:
            詳細 = QPushButton("詳細")
            詳細.clicked.connect(lambda _=False, r=row.job_id: self._open_detail(r))
            box.addWidget(詳細)
        line.setLayout(box)
        return line

    def _open_detail(self, id: str) -> None:
        from app.dto.detail_view import DetailView
        from ui.detail import DetailDialog

        view = self._detail(id) if self._detail is not None else None
        if not isinstance(view, DetailView) or self._act is None:
            self._word.setText("断り: その仕事はもうありません")
            return
        DetailDialog(view, self._act, parent=self).exec()
        self.refresh()
