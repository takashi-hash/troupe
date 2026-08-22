"""予定 — 先に何が来る？

設計: 設計/人に見えるもの.md §1「予定」・§3。

**引き出しの画面**（押しつけは今日だけ）。業務ルールの一覧と次の対象期間、
未作成のものが見える（F1）。押せるのは 版を積む・有効にする・止める——
人なら誰でも。版の欄は書かなければ**題材のデータが初期値**。
"""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
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

from app.dto.schedule_row import ScheduleRow

#: 操作の識別子 → 用語集の語。
操作の語 = {"add_version": "版を積む", "activate": "有効にする", "deactivate": "止める"}


class 予定を読む手(Protocol):
    def __call__(self) -> tuple[ScheduleRow, ...]: ...


class 決まりを押す手(Protocol):
    def __call__(self, what: str, name: str, version: int, fields: dict[str, str]) -> str | None:
        """通れば None、断られたら理由。fields は版の欄（空欄は題材の初期値）。"""
        ...


class VersionFormDialog(QDialog):
    """版の欄を書く小窓。**空欄は題材のデータが初期値**。"""

    欄 = (
        ("instruction", "やること"),
        ("source", "源（例: file:custom/名前/deps.txt）"),
        ("required_terms", "必ず含む語（読点区切り。{対象期間} と書ける）"),
        ("description", "説明の文"),
        ("cycle", "周期（weekly / monthly）"),
        ("days", "終えるまでの日数"),
        ("budget_calls", "使用上限（回数）"),
        ("budget_seconds", "使用上限（秒）"),
        ("owner", "受け持ちの人"),
        ("max_retries", "やり直しの上限"),
    )

    def __init__(self, rule: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"版を積む — {rule}")
        form = QFormLayout()
        self._inputs: dict[str, QLineEdit] = {}
        for key, label in self.欄:
            edit = QLineEdit()
            edit.setPlaceholderText("書かなければ題材の初期値")
            self._inputs[key] = edit
            form.addRow(label, edit)
        積む = QPushButton("版を積む")
        積む.clicked.connect(self.accept)
        form.addRow(積む)
        self.setLayout(form)

    def fields(self) -> dict[str, str]:
        return {k: e.text().strip() for k, e in self._inputs.items() if e.text().strip()}


class ScheduleScreen(QWidget):
    """予定の画面。読む手と押す手を注がれて並べるだけ。"""

    def __init__(self, fetch: 予定を読む手, act: 決まりを押す手) -> None:
        super().__init__()
        self._fetch = fetch
        self._act = act
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
            self._word.setText("業務ルールはまだありません——「版を積む」から始まります")
            新規 = QPushButton("版を積む（新しい業務ルール）")
            新規.clicked.connect(lambda: self._add_version(""))
            self._rows_box.addWidget(新規)
            return
        self._word.setText(f"業務ルール: {len(rows)}件")
        for row in rows:
            self._rows_box.addWidget(self._card(row))
        新規 = QPushButton("版を積む（新しい業務ルール）")
        新規.clicked.connect(lambda: self._add_version(""))
        self._rows_box.addWidget(新規)

    def _card(self, row: ScheduleRow) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        box = QVBoxLayout()
        有効 = f"有効: 版{row.active_version}" if row.active_version else "止まっている"
        box.addWidget(_bold(f"{row.rule}　［{有効}／最新: 版{row.version}］"))
        box.addWidget(_para(f"やること: {row.instruction}"))
        if row.next_period:
            box.addWidget(_para(f"次の対象期間: {row.next_period}"))
        buttons = QHBoxLayout()
        for action in row.actions:
            button = QPushButton(操作の語.get(action, action))
            if action == "add_version":
                button.clicked.connect(lambda _=False, r=row.rule: self._add_version(r))
            else:
                button.clicked.connect(
                    lambda _=False, a=action, r=row.rule, v=row.version: self._press(a, r, v, {})
                )
            buttons.addWidget(button)
        box.addLayout(buttons)
        card.setLayout(box)
        return card

    def _add_version(self, rule: str) -> None:
        名前 = rule
        if not 名前:
            dialog = QDialog(self)
            dialog.setWindowTitle("新しい業務ルール")
            form = QFormLayout()
            name_edit = QLineEdit()
            form.addRow("業務ルールの名", name_edit)
            進む = QPushButton("次へ")
            進む.clicked.connect(dialog.accept)
            form.addRow(進む)
            dialog.setLayout(form)
            if not dialog.exec():
                return
            名前 = name_edit.text().strip()
            if not 名前:
                self._word.setText("断り: 業務ルールの名が空です")
                return
        欄 = VersionFormDialog(名前, parent=self)
        if not 欄.exec():
            return
        self._press("add_version", 名前, 0, 欄.fields())

    def _press(self, action: str, name: str, version: int, fields: dict[str, str]) -> None:
        断り = self._act(action, name, version, fields)
        self._word.setText(f"断り: {断り}" if 断り else f"{操作の語.get(action, action)} — できた")
        if not 断り:
            self.refresh()


def _bold(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("font-weight: bold;")
    return label


def _para(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label
