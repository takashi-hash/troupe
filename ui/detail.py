"""詳細 — この仕事は誰が・いつ・何を・どうした？

設計: 設計/人に見えるもの.md §1「詳細」。**一覧の行から開く**（今日・検索などから）。
入っているものを出すだけ。出来事の全部と、質問・回答・見立ての本文——縮めない。
押せることは今日と同じ手で押す（§3: 承認する・差し戻す・答える・打ち切るは今日・詳細）。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.dto.detail_view import DetailView
from ui.today import Press
from ui.words import ACTION_WORDS, TEXT_FIELDS


class DetailDialog(QDialog):
    """詳細の窓。読み終わった DetailView を並べ、押す手（`Press`）で押す。"""

    def __init__(self, view: DetailView, act: Press, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"詳細 — {view.id}")
        self.resize(640, 560)
        self._act = act
        self._view = view
        self._word = QLabel()
        self._word.setWordWrap(True)

        body = QVBoxLayout()
        body.setAlignment(Qt.AlignmentFlag.AlignTop)
        body.addWidget(_para(f"やること: {view.instruction}"))
        body.addWidget(_para(f"状態: {view.state_name}　期日: {view.due}"))
        if view.assignee_name:
            body.addWidget(_para(f"担当: {view.assignee_name}"))
        if view.recheck_at:
            body.addWidget(_para(f"確かめ期日: {view.recheck_at}"))
        for 質問, 回答 in view.questions:
            body.addWidget(_para(f"質問: {質問}"))
            body.addWidget(_para(f"回答: {回答}" if 回答 is not None else "回答: （まだ）"))
        if view.result_body:
            body.addWidget(_para(f"成果: {view.result_body}"))
        if view.evidence_quote:
            body.addWidget(_para(f"根拠: {view.evidence_quote}"))
        for finding, reason in view.assessments:
            body.addWidget(_para(f"見立て: {finding}（{reason}）"))

        body.addWidget(_para("── 出来事の列（何が起きたか説明できる） ──"))
        for event in view.events:
            body.addWidget(_para(f"{event.at}　{event.by}　{event.what}"))

        host = QWidget()
        host.setLayout(body)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(host)

        buttons = QHBoxLayout()
        self._text = QLineEdit()
        needs = [w for a in view.actions if (w := TEXT_FIELDS.get(a))]
        if needs:
            self._text.setPlaceholderText("・".join(needs))
            buttons.addWidget(self._text, stretch=1)
        for action in view.actions:
            button = QPushButton(ACTION_WORDS.get(action, action))
            button.clicked.connect(lambda _=False, a=action: self._press(a))
            buttons.addWidget(button)

        outer = QVBoxLayout()
        outer.addWidget(self._word)
        outer.addWidget(scroll)
        outer.addLayout(buttons)
        self.setLayout(outer)

    def _press(self, action: str) -> None:
        断り = self._act(action, self._view.id, self._text.text())
        if 断り:
            self._word.setText(f"断り: {断り}")
        else:
            self.accept()  # できたら閉じる——一覧が開き直して新しい姿を見せる


def _para(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label
