"""今日 — いま私の判断と目が要るものは？

設計: 設計/人に見えるもの.md §1・§4・§5。

**入っているものを出し、押されたら文字で app を呼ぶだけ。**
- 本文（質問・成果・根拠・見立て）は**そのまま載せる——縮めない**
- 画面に出るのは用語集の語そのまま（状態の名・ボタンの語）
- 断られたら断られたと出す——**押して何も起きないのが一番わるい**
- 画面は常に導出——「更新」は開き直しと同じ。帳簿には書かない

app を直接 import しない——窓の組み立て（main.py）が「読む」「押す」の
2つの手を注ぐ。画面は手の中身を知らない。
"""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.dto.today_row import TodayRow

#: 操作の識別子 → 用語集の語。画面で言い換えない。
操作の語 = {
    "answer": "答える",
    "approve": "承認する",
    "send_back": "差し戻す",
    "abandon": "打ち切る",
}

#: 書く欄が要る操作と、その欄の名。
書く欄 = {"answer": "答え", "send_back": "差し戻す理由", "abandon": "打ち切る理由"}


class 読む手(Protocol):
    def __call__(self) -> tuple[TodayRow, ...]: ...


class 押す手(Protocol):
    def __call__(self, what: str, id: str, text: str) -> str | None:
        """通れば None、断られたら理由の文字。"""
        ...


class TodayScreen(QWidget):
    """今日の画面。読む手と押す手を注がれて、並べるだけ。"""

    def __init__(self, fetch: 読む手, act: 押す手, refresh_seconds: int = 60) -> None:
        super().__init__()
        self._fetch = fetch
        self._act = act
        self._word = QLabel()
        self._word.setWordWrap(True)
        self._rows_box = QVBoxLayout()
        self._rows_box.setAlignment(Qt.AlignmentFlag.AlignTop)

        rows_host = QWidget()
        rows_host.setLayout(self._rows_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(rows_host)

        更新 = QPushButton("更新")
        更新.clicked.connect(self.refresh)

        outer = QVBoxLayout()
        outer.addWidget(更新)
        outer.addWidget(self._word)
        outer.addWidget(scroll)
        self.setLayout(outer)

        # 開いているあいだは、ときどき開き直すのと同じ——帳簿には書かない。
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(refresh_seconds * 1000)
        self.refresh()

    def refresh(self) -> None:
        while self._rows_box.count():
            item = self._rows_box.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        rows = self._fetch()
        if not rows:
            self._word.setText("今日は空です")
            return
        self._word.setText(f"判断が要るもの: {len(rows)}件")
        for row in rows:
            self._rows_box.addWidget(self._card(row))

    def _card(self, row: TodayRow) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        box = QVBoxLayout()

        見出し = row.rule or row.request_head or row.id
        box.addWidget(_bold(f"{見出し}　{row.period or ''}　［{row.state_name}］　期日 {row.due}"))
        if row.question_body:
            box.addWidget(_para(f"質問: {row.question_body}"))
        if row.answer_body:
            box.addWidget(_para(f"回答: {row.answer_body}"))
        if row.result_body:
            box.addWidget(_para(f"成果: {row.result_body}"))
        if row.evidence_quote:
            box.addWidget(_para(f"根拠: {row.evidence_quote}"))
        for finding, reason in row.assessments:
            box.addWidget(_para(f"見立て: {finding}（{reason}）"))
        if row.retries_exhausted:
            box.addWidget(_para("やり直しは尽きています"))

        buttons = QHBoxLayout()
        text_input = QLineEdit()
        needs_text = [w for a in row.actions if (w := 書く欄.get(a))]
        if needs_text:
            text_input.setPlaceholderText("・".join(needs_text))
            buttons.addWidget(text_input, stretch=1)
        for action in row.actions:
            button = QPushButton(操作の語.get(action, action))
            button.clicked.connect(
                lambda _=False, a=action, r=row.id, t=text_input: self._press(a, r, t.text())
            )
            buttons.addWidget(button)
        box.addLayout(buttons)
        card.setLayout(box)
        return card

    def _press(self, action: str, id: str, text: str) -> None:
        断り = self._act(action, id, text)
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

