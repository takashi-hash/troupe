"""検索 — あの仕事はどこ？

設計: 設計/人に見えるもの.md §1「検索」・§2「絞り込みの条件」「検索の行」。
**引き出しの画面**（押しつけは今日だけ）。終わったものも含めて引く（F1）。
欄はどれも文字——空の欄は絞らない。状態は用語集の語で書く（語→識別子の橋は app）。
行から詳細が開く。
"""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.dto.row_filter import RowFilter
from app.dto.search_row import SearchRow
from ui.today import Press, FetchDetail


class SearchJobs(Protocol):
    def __call__(self, filter: RowFilter) -> tuple[SearchRow, ...]: ...


class SearchScreen(QWidget):
    """検索の画面。絞り込みの条件を文字で渡し、返った行を並べるだけ。"""

    def __init__(
        self,
        search: SearchJobs,
        act: Press | None = None,
        detail: FetchDetail | None = None,
    ) -> None:
        super().__init__()
        self._search = search
        self._act = act
        self._detail = detail
        self._word = QLabel()
        self._word.setWordWrap(True)
        self._rows_box = QVBoxLayout()
        self._rows_box.setAlignment(Qt.AlignmentFlag.AlignTop)

        form = QFormLayout()
        self._keyword = QLineEdit()
        self._state = QLineEdit()
        self._state.setPlaceholderText("用語集の語で（例: 終わった）")
        self._rule = QLineEdit()
        self._assignee = QLineEdit()
        form.addRow("キーワード", self._keyword)
        form.addRow("状態", self._state)
        form.addRow("業務ルール", self._rule)
        form.addRow("担当", self._assignee)
        引く = QPushButton("検索")
        引く.clicked.connect(self.refresh)
        form.addRow(引く)

        host = QWidget()
        host.setLayout(self._rows_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(host)

        outer = QVBoxLayout()
        outer.addLayout(form)
        outer.addWidget(self._word)
        outer.addWidget(scroll)
        self.setLayout(outer)

    def refresh(self) -> None:
        while self._rows_box.count():
            item = self._rows_box.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.setParent(None)  # すぐ画面から外す——deleteLater 待ちの重なりを見せない
                widget.deleteLater()
        条件 = RowFilter(
            keyword=self._keyword.text().strip() or None,
            state_label=self._state.text().strip() or None,
            rule=self._rule.text().strip() or None,
            assignee=self._assignee.text().strip() or None,
        )
        rows = self._search(条件)
        if not rows:
            self._word.setText("見つかりませんでした")
            return
        self._word.setText(f"見つかった: {len(rows)}件")
        for row in rows:
            self._rows_box.addWidget(self._card(row))

    def _card(self, row: SearchRow) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        box = QVBoxLayout()
        担当 = f"　担当 {row.assignee_name}" if row.assignee_name else ""
        頭 = QLabel(f"{row.head}　［{row.state_name}］{担当}　期日 {row.due}")
        頭.setWordWrap(True)
        頭.setStyleSheet("font-weight: bold;")
        box.addWidget(頭)
        やること = QLabel(f"やること: {row.instruction}")
        やること.setWordWrap(True)
        やること.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(やること)
        if self._detail is not None and self._act is not None:
            buttons = QHBoxLayout()
            詳細 = QPushButton("詳細")
            詳細.clicked.connect(lambda _=False, r=row.id: self._open_detail(r))
            buttons.addWidget(詳細)
            buttons.addStretch(1)
            box.addLayout(buttons)
        card.setLayout(box)
        return card

    def _open_detail(self, id: str) -> None:
        from app.dto.detail_view import DetailView
        from ui.detail import DetailDialog

        view = self._detail(id) if self._detail is not None else None
        if not isinstance(view, DetailView) or self._act is None:
            self._word.setText("断り: その仕事はもうありません")
            return
        DetailDialog(view, self._act, parent=self).exec()
