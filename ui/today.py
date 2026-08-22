"""今日 — いま私の判断と目が要るものは？

設計: 設計/人に見えるもの.md §1・§4・§5。

**入っているものを出し、押されたら文字で app を呼ぶだけ。**
- 本文（質問・成果・根拠・見立て）は**そのまま載せる——縮めない**
- 画面に出るのは用語集の語そのまま（状態の名・ボタンの語）
- 断られたら断られたと出す——**押して何も起きないのが一番わるい**
- 画面は常に導出——「更新」は開き直しと同じ。帳簿には書かない

app を直接 import しない——窓の組み立て（main.py）が手（読む・押す・詳細を読む）を
注ぐ。画面は手の中身を知らない。
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
from ui.words import ACTION_WORDS, TEXT_FIELDS


class FetchToday(Protocol):
    def __call__(self) -> tuple[TodayRow, ...]: ...


class Press(Protocol):
    def __call__(self, what: str, id: str, text: str) -> str | None:
        """通れば None、断られたら理由の文字。"""
        ...


class FetchDetail(Protocol):
    def __call__(self, id: str) -> object | None:
        """1件の詳細（DetailView）。無ければ None。"""
        ...


class TodayScreen(QWidget):
    """今日の画面。読む手と押す手を注がれて、並べるだけ。"""

    def __init__(
        self,
        fetch: FetchToday,
        act: Press,
        detail: FetchDetail | None = None,
        refresh_seconds: int = 60,
    ) -> None:
        super().__init__()
        self._fetch = fetch
        self._act = act
        self._detail = detail
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
                widget.setParent(None)  # すぐ画面から外す——deleteLater 待ちの重なりを見せない
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
        担当 = f"　担当 {row.assignee_name}" if row.assignee_name else ""
        box.addWidget(_bold(f"{見出し}　{row.period or ''}　［{row.state_name}］{担当}　期日 {row.due}"))
        box.addWidget(_para(f"やること: {row.instruction}"))
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
        if row.recheck_at:
            box.addWidget(_para(f"確かめ期日: {row.recheck_at}"))
        box.addWidget(
            _para(
                f"使った量: {row.spent_calls}回・{row.spent_seconds}秒"
                f"（上限 {row.budget_calls}回・{row.budget_seconds}秒）"
            )
        )
        if row.retries_exhausted:
            box.addWidget(_para("やり直しは尽きています"))

        buttons = QHBoxLayout()
        text_input = QLineEdit()
        needs_text = [w for a in row.actions if (w := TEXT_FIELDS.get(a))]
        if needs_text:
            text_input.setPlaceholderText("・".join(needs_text))
            buttons.addWidget(text_input, stretch=1)
        for action in row.actions:
            button = QPushButton(ACTION_WORDS.get(action, action))
            button.clicked.connect(
                lambda _=False, a=action, r=row.id, t=text_input: self._press(a, r, t.text())
            )
            buttons.addWidget(button)
        if self._detail is not None:
            詳細 = QPushButton("詳細")
            詳細.clicked.connect(lambda _=False, r=row.id: self._open_detail(r))
            buttons.addWidget(詳細)
        box.addLayout(buttons)
        card.setLayout(box)
        return card

    def _open_detail(self, id: str) -> None:
        from app.dto.detail_view import DetailView
        from ui.detail import DetailDialog

        view = self._detail(id) if self._detail is not None else None
        if not isinstance(view, DetailView):
            self._word.setText("断り: その仕事はもうありません")
            return
        DetailDialog(view, self._act, parent=self).exec()
        self.refresh()

    def _press(self, action: str, id: str, text: str) -> None:
        断り = self._act(action, id, text)
        if not 断り:
            self.refresh()  # 開き直しが先——結果の言葉を上書きで消さない
        self._word.setText(f"断り: {断り}" if 断り else f"{ACTION_WORDS.get(action, action)} — できた")


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

