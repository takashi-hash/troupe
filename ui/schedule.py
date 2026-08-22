"""予定 — 先に何が来る？

設計: 設計/人に見えるもの.md §1「予定」・§3。

**引き出しの画面**（押しつけは今日だけ）。業務ルールの一覧と次の対象期間・未作成のもの、
**作られた仕事の列（終点以外）**が見える（F1）。押せるのは 版を積む・有効にする・止める・
**頼む**——人なら誰でも。頼んだ直後の仕事は下段の列に見え、行から詳細が開く。
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
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from ui.today import Press, FetchDetail
from ui.words import ACTION_WORDS


class FetchSchedule(Protocol):
    def __call__(self) -> tuple[ScheduleRow, ...]: ...


class PressRule(Protocol):
    def __call__(self, what: str, name: str, version: int, fields: dict[str, str]) -> str | None:
        """通れば None、断られたら理由。fields は版の欄（空欄は題材の初期値）。"""
        ...


class RequestJob(Protocol):
    def __call__(self, body: str, fields: dict[str, str]) -> str | None:
        """頼む——一度きりの仕事。通れば None、断られたら理由。"""
        ...


class FetchUpcoming(Protocol):
    def __call__(self) -> tuple[SearchRow, ...]:
        """作られた仕事の列（終点以外）。"""
        ...


class VersionFormDialog(QDialog):
    """版の欄を書く小窓。**空欄は題材のデータが初期値**。"""

    欄 = (
        ("instruction", "やること"),
        ("source", "源（例: file:custom/名前/deps.txt）"),
        ("required_terms", "必ず含む語（読点区切り。{対象期間} と書ける）"),
        ("description", "説明の文"),
        ("cycle", "周期（週 か 月）"),
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


class RequestFormDialog(QDialog):
    """頼む小窓。頼む中身と版の欄ぜんぶ——**依頼発に題材は無い、欄はぜんぶ人が書く**。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("頼む — 一度きりの仕事")
        form = QFormLayout()
        self._body = QPlainTextEdit()
        self._body.setPlaceholderText("頼む中身")
        form.addRow("頼む中身", self._body)
        self._inputs: dict[str, QLineEdit] = {}
        案内 = {
            "instruction": "書かなければ頼む中身がそのまま",
            "source": "書く（例: file:custom/名前/deps.txt）",
            "required_terms": "書く——成果に必ず入っているべき語",
            "description": "書かなくてよい",
            "cycle": "書かなければ 週",
            "days": "書かなければ 3",
            "budget_calls": "書かなければ 20",
            "budget_seconds": "書かなければ 600",
            "owner": "書かなければ頼んだ人",
            "max_retries": "書かなければ 2",
        }
        for key, label in VersionFormDialog.欄:
            if key == "required_terms":
                label = "必ず含む語（読点区切り。依頼発に {対象期間} は書けない）"
            edit = QLineEdit()
            edit.setPlaceholderText(案内.get(key, "書く"))
            self._inputs[key] = edit
            form.addRow(label, edit)
        頼む = QPushButton("頼む")
        頼む.clicked.connect(self.accept)
        form.addRow(頼む)
        self.setLayout(form)

    def body(self) -> str:
        return self._body.toPlainText().strip()

    def fields(self) -> dict[str, str]:
        return {k: e.text().strip() for k, e in self._inputs.items() if e.text().strip()}


class ScheduleScreen(QWidget):
    """予定の画面。読む手と押す手を注がれて並べるだけ。"""

    def __init__(
        self,
        fetch: FetchSchedule,
        act: PressRule,
        request: RequestJob | None = None,
        upcoming: FetchUpcoming | None = None,
        press: Press | None = None,
        detail: FetchDetail | None = None,
    ) -> None:
        super().__init__()
        self._fetch = fetch
        self._act = act
        self._request = request
        self._upcoming = upcoming
        self._press_job = press
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
                widget.setParent(None)  # すぐ画面から外す——deleteLater 待ちの重なりを見せない
                widget.deleteLater()
        rows = self._fetch()
        if not rows:
            self._word.setText("業務ルールはまだありません——「版を積む」から始まります")
            新規 = QPushButton("版を積む（新しい業務ルール）")
            新規.clicked.connect(lambda: self._add_version(""))
            self._rows_box.addWidget(新規)
            if self._request is not None:
                頼む = QPushButton(f"{ACTION_WORDS['request']}（一度きりの仕事）")
                頼む.clicked.connect(self._ask_request)
                self._rows_box.addWidget(頼む)
            self._show_upcoming()
            return
        self._word.setText(f"業務ルール: {len(rows)}件")
        for row in rows:
            self._rows_box.addWidget(self._card(row))
        新規 = QPushButton("版を積む（新しい業務ルール）")
        新規.clicked.connect(lambda: self._add_version(""))
        self._rows_box.addWidget(新規)
        if self._request is not None:
            頼む = QPushButton(f"{ACTION_WORDS['request']}（一度きりの仕事）")
            頼む.clicked.connect(self._ask_request)
            self._rows_box.addWidget(頼む)
        self._show_upcoming()

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
            button = QPushButton(ACTION_WORDS.get(action, action))
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

    def _show_upcoming(self) -> None:
        """作られた仕事の列（終点以外）。頼んだ直後の行方がここに見える。"""
        if self._upcoming is None:
            return
        jobs = self._upcoming()
        見出し = QLabel(f"── 来ている仕事: {len(jobs)}件（終点以外） ──")
        見出し.setWordWrap(True)
        self._rows_box.addWidget(見出し)
        for job in jobs:
            line = QWidget()
            box = QHBoxLayout()
            box.setContentsMargins(0, 0, 0, 0)
            担当 = f"　担当 {job.assignee_name}" if job.assignee_name else ""
            文 = f"{job.head}　［{job.state_name}］{担当}　期日 {job.due}"
            if len(文) > 80:
                文 = 文[:80] + "…"  # 折り返さない——全文は行の詳細で読める
            label = QLabel(文)
            label.setWordWrap(False)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            box.addWidget(label, stretch=1)
            if self._detail is not None and self._press_job is not None:
                詳細 = QPushButton("詳細")
                詳細.clicked.connect(lambda _=False, r=job.id: self._open_detail(r))
                box.addWidget(詳細)
            line.setLayout(box)
            self._rows_box.addWidget(line)

    def _open_detail(self, id: str) -> None:
        from app.dto.detail_view import DetailView
        from ui.detail import DetailDialog

        view = self._detail(id) if self._detail is not None else None
        if not isinstance(view, DetailView) or self._press_job is None:
            self._word.setText("断り: その仕事はもうありません")
            return
        DetailDialog(view, self._press_job, parent=self).exec()
        self.refresh()

    def _ask_request(self) -> None:
        if self._request is None:
            return
        小窓 = RequestFormDialog(parent=self)
        if not 小窓.exec():
            return
        断り = self._request(小窓.body(), 小窓.fields())
        if not 断り:
            self.refresh()  # 開き直しが先——結果の言葉を上書きで消さない
        self._word.setText(
            f"断り: {断り}" if 断り else f"{ACTION_WORDS['request']} — できた（行方は履歴・検索に）"
        )

    def _press(self, action: str, name: str, version: int, fields: dict[str, str]) -> None:
        断り = self._act(action, name, version, fields)
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
