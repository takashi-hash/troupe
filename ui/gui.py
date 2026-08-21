"""画面 — 読む4枚のネイティブ GUI（PySide6）。

見た目の正本は 設計/10_画面/デザイン案.dc.html。紙の色・赤・「操作できる青」・
点線＝まだ作られていない、をそのまま写す。画面は常に導出——1秒ごとに帳簿を読み直す。
書く口（チャット）は、その仕組みが効くまで入口が現れない。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from domain.search import SearchCriteria
from app.manager import surface
from domain.ports import SheetSource
from ui.sheets import (
    JobSheet,
    Row,
    Section,
    history_sections,
    job_sheet,
    morning_count,
    morning_sections,
    outlook_sections,
    search_options,
    search_sections,
    state_kind_of_label,
)

VIEWER = "人/座長"

INK = "#2a2723"
PAPER = "#f8f6f1"
SIDE = "#f2efe8"
CARD = "#fffefb"
RED = "#b4382c"
RED_BG = "#fdf1ef"
BLUE = "#3a5a8c"
SERIF = "'Hiragino Mincho ProN','Shippori Mincho',serif"
SANS = "'Hiragino Kaku Gothic ProN','Zen Kaku Gothic New',sans-serif"
MONO = "'Menlo','SF Mono',monospace"

QSS = f"""
* {{ font-family: {SANS}; color: {INK}; font-size: 15px; }}
QMainWindow, QStackedWidget, QScrollArea, QWidget#page {{ background: {PAPER}; }}
QWidget#sidebar {{ background: {SIDE}; border-right: 1px solid rgba(42,39,35,36); }}
QLabel#brand {{ font-family: {SERIF}; font-size: 23px; font-weight: 600; }}
QLabel#boardName {{ font-family: {MONO}; font-size: 13px; color: rgba(42,39,35,128); }}
QPushButton.nav {{ background: transparent; border: none; text-align: left; padding: 12px 20px;
  font-size: 17px; color: rgba(42,39,35,200); border-left: 3px solid transparent; }}
QPushButton.nav:hover {{ background: rgba(42,39,35,12); }}
QPushButton.nav[current="true"] {{ border-left: 3px solid {INK}; color: {INK}; font-weight: 600; }}
QLabel#badge {{ background: {RED}; color: white; border-radius: 11px; padding: 2px 9px;
  font-family: {MONO}; font-size: 13px; }}
QLabel.legend {{ font-size: 13px; color: rgba(42,39,35,135); }}
QLabel#pageTitle {{ font-family: {SERIF}; font-size: 34px; font-weight: 600; }}
QLabel#pageNote {{ font-size: 15px; color: rgba(42,39,35,150); }}
QFrame#rule {{ background: rgba(42,39,35,36); max-height: 1px; min-height: 1px; border: none; }}
QLabel.sectionLabel {{ font-size: 17px; font-weight: 600; }}
QLabel.sectionLabelRed {{ font-size: 17px; font-weight: 600; color: {RED}; }}
QLabel.sectionNote {{ font-size: 14px; color: rgba(42,39,35,135); }}
QFrame.card {{ background: {CARD}; border: 1px solid rgba(42,39,35,41); border-radius: 4px; }}
QFrame.cardRed {{ background: {RED_BG}; border: 1px solid rgba(180,56,44,90);
  border-left: 4px solid {RED}; border-radius: 4px; }}
QFrame.cardDashed {{ background: rgba(255,255,255,102);
  border: 1px dashed rgba(42,39,35,110); border-radius: 4px; }}
QLabel.cardTitle {{ font-size: 17px; }}
QLabel.cardTitleDim {{ font-size: 17px; color: rgba(42,39,35,150); }}
QLabel.cardMeta {{ font-family: {MONO}; font-size: 13px; color: rgba(42,39,35,145); }}
QLabel.kindRed {{ font-size: 13px; font-weight: 600; color: {RED}; }}
QLabel.kind {{ font-size: 13px; color: rgba(42,39,35,145); }}
QPushButton.write {{ background: {BLUE}; color: white; border: none; border-radius: 4px;
  padding: 11px 30px; font-size: 16px; font-weight: 600; }}
QPushButton.write:hover {{ background: #2b4468; }}
QLabel#stateChip {{ border: 1px solid {BLUE}; color: {BLUE}; border-radius: 4px;
  padding: 6px 16px; font-size: 15px; }}
QLabel.timeline {{ font-family: {MONO}; font-size: 15px; color: rgba(42,39,35,185); }}
QLabel.timelineRed {{ font-family: {MONO}; font-size: 15px; color: {RED}; font-weight: 600; }}
QFrame#timelineBar {{ background: rgba(42,39,35,51); max-width: 1px; min-width: 1px; border: none; }}
QLabel.factLabel {{ font-size: 13px; color: rgba(42,39,35,135); }}
QLabel.factValue {{ font-size: 16px; }}
QLabel#emptyNote {{ font-size: 16px; color: rgba(42,39,35,120); }}
QLineEdit {{ background: {CARD}; border: 1px solid rgba(42,39,35,60); border-radius: 4px;
  padding: 10px 14px; font-size: 16px; }}
QLineEdit:focus {{ border: 1px solid {BLUE}; }}
QComboBox {{ background: {CARD}; border: 1px solid rgba(42,39,35,60); border-radius: 4px;
  padding: 9px 12px; font-size: 15px; min-width: 150px; }}
QLabel.filterLabel {{ font-size: 13px; color: rgba(42,39,35,135); }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: rgba(42,39,35,60); border-radius: 6px; min-height: 40px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

_PAGES = ("今日", "予定", "履歴", "検索", "詳細")


def _clear(layout: QVBoxLayout, keep: QWidget | None = None) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            break
        widget = item.widget()
        if widget is None or widget is keep:
            continue  # 絞り込みの帯は作り直さない（打ちかけの字が消えないように）
        widget.deleteLater()


class Card(QFrame):
    def __init__(
        self,
        row: Row,
        on_open: Callable[[str], None],
        on_action: Callable[[str, str], None],
    ) -> None:
        super().__init__()
        self.setProperty("class", "cardRed" if row.red else "cardDashed" if row.dashed else "card")
        self._job_id = row.job_id
        self._on_open = on_open
        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(18)
        body = QVBoxLayout()
        body.setSpacing(6)
        if row.kind_label:
            kind = QLabel(row.kind_label)
            kind.setProperty("class", "kindRed" if row.red else "kind")
            body.addWidget(kind)
        title = QLabel(row.title)
        title.setProperty("class", "cardTitleDim" if row.dashed else "cardTitle")
        title.setWordWrap(True)
        body.addWidget(title)
        if row.meta:
            meta = QLabel(row.meta)
            meta.setProperty("class", "cardMeta")
            meta.setWordWrap(True)
            body.addWidget(meta)
        outer.addLayout(body, 1)
        if row.action and row.job_id:
            button = QPushButton(row.action)
            button.setProperty("class", "write")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            action, job_id = row.action, row.job_id
            button.clicked.connect(lambda _=False: on_action(action, job_id))
            outer.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        if row.job_id:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt の流儀)
        if self._job_id:
            self._on_open(self._job_id)
        super().mouseReleaseEvent(event)


class Page(QScrollArea):
    """見出し＋節の並び。中身は毎回、導出から作り直す"""

    def __init__(
        self,
        title: str,
        on_open: Callable[[str], None],
        on_action: Callable[[str, str], None],
        filters: FilterBar | None = None,
    ) -> None:
        super().__init__()
        self._on_action = on_action
        self._filters = filters
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._on_open = on_open
        page = QWidget()
        page.setObjectName("page")
        self._layout = QVBoxLayout(page)
        self._layout.setContentsMargins(52, 36, 52, 48)
        self._layout.setSpacing(18)
        self._title = title
        self.setWidget(page)

    def populate(self, note: str, sections: list[Section], empty_note: str) -> None:
        _clear(self._layout, keep=self._filters)
        title = QLabel(self._title)
        title.setObjectName("pageTitle")
        self._layout.addWidget(title)
        note_label = QLabel(note)
        note_label.setObjectName("pageNote")
        note_label.setWordWrap(True)
        self._layout.addWidget(note_label)
        if self._filters is not None:
            self._layout.addWidget(self._filters)
        rule = QFrame()
        rule.setObjectName("rule")
        self._layout.addWidget(rule)
        if not sections:
            empty = QLabel(empty_note)
            empty.setObjectName("emptyNote")
            self._layout.addWidget(empty)
        for section in sections:
            head = QHBoxLayout()
            head.setSpacing(12)
            label = QLabel(section.label)
            label.setProperty("class", "sectionLabelRed" if section.red else "sectionLabel")
            head.addWidget(label)
            if section.note:
                sub = QLabel(section.note)
                sub.setProperty("class", "sectionNote")
                head.addWidget(sub)
            head.addStretch(1)
            holder = QWidget()
            holder.setLayout(head)
            self._layout.addWidget(holder)
            for row in section.rows:
                self._layout.addWidget(Card(row, self._on_open, self._on_action))
        self._layout.addStretch(1)


class FilterBar(QWidget):
    """絞り込み — 枚に出ているものを、検索と同じキーで狭める。枚ごとに別の絞り方を作らない"""

    def __init__(self, on_change: Callable[[], None], with_keyword: bool = True) -> None:
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)
        self._keyword: QLineEdit | None = None
        if with_keyword:
            self._keyword = QLineEdit()
            self._keyword.setPlaceholderText("キーワード")
            self._keyword.textChanged.connect(lambda _: on_change())
            row.addWidget(self._keyword, 1)
        self._state = _labeled_combo("状態", row, on_change)
        self._definition = _labeled_combo("業務ルール", row, on_change)
        self._assignee = _labeled_combo("担当", row, on_change)
        row.addStretch(0)

    def criteria(self) -> SearchCriteria:
        """画面の欄から検索条件を作る（検索と同じ形）"""
        return SearchCriteria(
            keyword=self._keyword.text().strip() if self._keyword else "",
            state_kind=state_kind_of_label(_chosen(self._state)),
            definition_name=_chosen(self._definition),
            assignee=_chosen(self._assignee),
        )

    def set_options(self, states: list[str], definitions: list[str], assignees: list[str]) -> None:
        """絞り込みの選択肢を入れ替える（帳簿から導いたもの）"""
        for combo, values in (
            (self._state, states),
            (self._definition, definitions),
            (self._assignee, assignees),
        ):
            _fill_combo(combo, values)


def _chosen(combo: QComboBox) -> str:
    text = combo.currentText()
    return "" if text == "すべて" else text


def _fill_combo(combo: QComboBox, values: list[str]) -> None:
    if [combo.itemText(i) for i in range(1, combo.count())] == values:
        return  # 変わっていないなら触らない（選択が飛ばないように）
    chosen = combo.currentText()
    combo.blockSignals(True)
    combo.clear()
    combo.addItem("すべて")
    combo.addItems(values)
    index = combo.findText(chosen)
    combo.setCurrentIndex(index if index >= 0 else 0)
    combo.blockSignals(False)


def _labeled_combo(label: str, row: QHBoxLayout, on_change: Callable[[], None]) -> QComboBox:
    box = QVBoxLayout()
    box.setSpacing(5)
    caption = QLabel(label)
    caption.setProperty("class", "filterLabel")
    combo = QComboBox()
    combo.addItem("すべて")
    combo.currentIndexChanged.connect(lambda _: on_change())
    box.addWidget(caption)
    box.addWidget(combo)
    holder = QWidget()
    holder.setLayout(box)
    row.addWidget(holder)
    return combo


class SearchPage(QScrollArea):
    """検索 — 完了も含めたすべてのタスクを、モデルの欄で絞って引く"""

    def __init__(self, on_open: Callable[[str], None], on_change: Callable[[], None]) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._on_open = on_open
        page = QWidget()
        page.setObjectName("page")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(52, 36, 52, 48)
        outer.setSpacing(18)

        title = QLabel("検索")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        note = QLabel("完了したタスクも含めて探せます。絞り込みの軸は、モデルにある欄だけです。")
        note.setObjectName("pageNote")
        note.setWordWrap(True)
        outer.addWidget(note)

        self._keyword = QLineEdit()
        self._keyword.setPlaceholderText("キーワード（業務ルールの名・成果物の中身・エラーの理由）")
        self._keyword.textChanged.connect(lambda _: on_change())
        outer.addWidget(self._keyword)

        filters = QHBoxLayout()
        filters.setSpacing(14)
        self._state = self._combo("状態", filters, on_change)
        self._definition = self._combo("業務ルール", filters, on_change)
        self._assignee = self._combo("担当", filters, on_change)
        filters.addStretch(1)
        holder = QWidget()
        holder.setLayout(filters)
        outer.addWidget(holder)

        rule = QFrame()
        rule.setObjectName("rule")
        outer.addWidget(rule)

        self._results = QVBoxLayout()
        self._results.setSpacing(18)
        results_holder = QWidget()
        results_holder.setLayout(self._results)
        outer.addWidget(results_holder)
        outer.addStretch(1)
        self.setWidget(page)

    def _combo(self, label: str, row: QHBoxLayout, on_change: Callable[[], None]) -> QComboBox:
        box = QVBoxLayout()
        box.setSpacing(5)
        caption = QLabel(label)
        caption.setProperty("class", "filterLabel")
        combo = QComboBox()
        combo.addItem("すべて")
        combo.currentIndexChanged.connect(lambda _: on_change())
        box.addWidget(caption)
        box.addWidget(combo)
        holder = QWidget()
        holder.setLayout(box)
        row.addWidget(holder)
        return combo

    def criteria(self) -> SearchCriteria:
        """画面の欄から検索条件を作る"""
        return SearchCriteria(
            keyword=self._keyword.text().strip(),
            state_kind=state_kind_of_label(self._chosen(self._state)),
            definition_name=self._chosen(self._definition),
            assignee=self._chosen(self._assignee),
        )

    @staticmethod
    def _chosen(combo: QComboBox) -> str:
        text = combo.currentText()
        return "" if text == "すべて" else text

    def set_options(self, states: list[str], definitions: list[str], assignees: list[str]) -> None:
        """絞り込みの選択肢を入れ替える（帳簿から導いたもの）"""
        for combo, values in (
            (self._state, states),
            (self._definition, definitions),
            (self._assignee, assignees),
        ):
            if [combo.itemText(i) for i in range(1, combo.count())] == values:
                continue  # 変わっていないなら触らない（選択が飛ばないように）
            chosen = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("すべて")
            combo.addItems(values)
            index = combo.findText(chosen)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    def populate(self, sections: list[Section], empty_note: str) -> None:
        _clear(self._results)
        if not sections:
            empty = QLabel(empty_note)
            empty.setObjectName("emptyNote")
            self._results.addWidget(empty)
        for section in sections:
            label = QLabel(section.label)
            label.setProperty("class", "sectionLabel")
            self._results.addWidget(label)
            if section.note:
                sub = QLabel(section.note)
                sub.setProperty("class", "sectionNote")
                self._results.addWidget(sub)
            for row in section.rows:
                self._results.addWidget(Card(row, self._on_open, lambda *_: None))


class JobSheetPage(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        page = QWidget()
        page.setObjectName("page")
        self._layout = QVBoxLayout(page)
        self._layout.setContentsMargins(52, 36, 52, 48)
        self._layout.setSpacing(18)
        self.setWidget(page)

    def populate(self, sheet: JobSheet | None) -> None:
        _clear(self._layout)
        if sheet is None:
            title = QLabel("詳細")
            title.setObjectName("pageTitle")
            self._layout.addWidget(title)
            empty = QLabel("「今日」や「予定」でタスクを選ぶと、ここに内容と履歴が出ます。")
            empty.setObjectName("emptyNote")
            self._layout.addWidget(empty)
            self._layout.addStretch(1)
            return
        crumb = QLabel(f"タスクID {sheet.job_id}")
        crumb.setProperty("class", "cardMeta")
        self._layout.addWidget(crumb)
        head = QHBoxLayout()
        title = QLabel(sheet.title)
        title.setObjectName("pageTitle")
        head.addWidget(title, 1)
        chip = QLabel(sheet.state_label)
        chip.setObjectName("stateChip")
        head.addWidget(chip, 0, Qt.AlignmentFlag.AlignTop)
        holder = QWidget()
        holder.setLayout(head)
        self._layout.addWidget(holder)
        rule = QFrame()
        rule.setObjectName("rule")
        self._layout.addWidget(rule)

        facts = QFrame()
        facts.setProperty("class", "card")
        facts_layout = QVBoxLayout(facts)
        facts_layout.setContentsMargins(20, 16, 20, 16)
        facts_layout.setSpacing(10)
        for label, value in sheet.facts:
            fact_label = QLabel(label)
            fact_label.setProperty("class", "factLabel")
            fact_value = QLabel(value)
            fact_value.setProperty("class", "factValue")
            fact_value.setWordWrap(True)
            facts_layout.addWidget(fact_label)
            facts_layout.addWidget(fact_value)
        self._layout.addWidget(facts)

        if sheet.artifacts:
            section = QLabel("成果物")
            section.setProperty("class", "sectionLabel")
            self._layout.addWidget(section)
            for artifact in sheet.artifacts:
                card = QFrame()
                card.setProperty("class", "card")
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(20, 14, 20, 14)
                card_layout.addWidget(QLabel(artifact))
                self._layout.addWidget(card)

        section = QLabel("履歴")
        section.setProperty("class", "sectionLabel")
        self._layout.addWidget(section)
        line = QHBoxLayout()
        bar = QFrame()
        bar.setObjectName("timelineBar")
        line.addWidget(bar)
        events_layout = QVBoxLayout()
        events_layout.setSpacing(9)
        for when, label, red in sheet.timeline:
            entry = QLabel(f"{when}　{label}")
            entry.setProperty("class", "timelineRed" if red else "timeline")
            events_layout.addWidget(entry)
        line.addSpacing(18)
        line.addLayout(events_layout, 1)
        holder2 = QWidget()
        holder2.setLayout(line)
        self._layout.addWidget(holder2)
        footer = QLabel("この画面は表示のみです。承認は「今日」から行います。")
        footer.setObjectName("emptyNote")
        self._layout.addWidget(footer)
        self._layout.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self, source: SheetSource, on_action: Callable[[str, str], str | None]) -> None:
        super().__init__()
        self._source = source
        self._on_action = self._wrap(on_action)
        self._selected_job: str | None = None
        self._stamp: object = None
        self.setWindowTitle("Ichiza（一座）")
        self.resize(1440, 950)
        self.setMinimumSize(1100, 720)

        self._nav_buttons: list[QPushButton] = []
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 26, 0, 20)
        side_layout.setSpacing(0)
        brand_box = QVBoxLayout()
        brand_box.setContentsMargins(20, 0, 20, 24)
        brand_box.setSpacing(4)
        brand = QLabel("一座")
        brand.setObjectName("brand")
        board_name = QLabel("ボード: 運転")
        board_name.setObjectName("boardName")
        brand_box.addWidget(brand)
        brand_box.addWidget(board_name)
        brand_holder = QWidget()
        brand_holder.setLayout(brand_box)
        side_layout.addWidget(brand_holder)

        self._badge = QLabel("")
        self._badge.setObjectName("badge")
        for index, name in enumerate(_PAGES):
            button = QPushButton(name)
            button.setProperty("class", "nav")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, i=index: self._switch(i))
            if name == "今日":
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 18, 0)
                row.setSpacing(0)
                row.addWidget(button, 1)
                row.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignVCenter)
                holder = QWidget()
                holder.setLayout(row)
                side_layout.addWidget(holder)
            else:
                side_layout.addWidget(button)
            self._nav_buttons.append(button)

        side_layout.addStretch(1)
        legend_box = QVBoxLayout()
        legend_box.setContentsMargins(20, 14, 20, 0)
        legend_box.setSpacing(7)
        for text in ("赤 — 要対応（エラー・不一致）", "青 — 操作できる場所", "点線 — まだ作成されていない"):
            legend = QLabel(text)
            legend.setProperty("class", "legend")
            legend_box.addWidget(legend)
        legend_holder = QWidget()
        legend_holder.setLayout(legend_box)
        side_layout.addWidget(legend_holder)

        self._stack = QStackedWidget()
        redraw = lambda: self._refresh(force=True)  # noqa: E731
        self._morning = Page("今日", self._open_job, self._on_action)  # 押しつけなので絞れない
        self._outlook_filters = FilterBar(redraw)
        self._outlook = Page("予定", self._open_job, self._on_action, self._outlook_filters)
        self._history_filters = FilterBar(redraw)
        self._history = Page("履歴", self._open_job, self._on_action, self._history_filters)
        self._search = SearchPage(self._open_job, redraw)
        self._job_page = JobSheetPage()
        for widget in (
            self._morning,
            self._outlook,
            self._history,
            self._search,
            self._job_page,
        ):
            self._stack.addWidget(widget)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(sidebar)
        root_layout.addWidget(self._stack, 1)
        self.setCentralWidget(root)
        self._switch(0)

        timer = QTimer(self)
        timer.timeout.connect(self._refresh)
        timer.start(1000)
        self._refresh(force=True)

    def _switch(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, button in enumerate(self._nav_buttons):
            button.setProperty("current", "true" if i == index else "false")
            style = button.style()
            style.unpolish(button)
            style.polish(button)
        self._refresh(force=True)

    def _wrap(self, on_action: Callable[[str, str], str | None]) -> Callable[[str, str], None]:
        def run(action: str, job_id: str) -> None:
            refused = on_action(action, job_id)
            # 断られたら理由を出す——押して何も起きないのが一番わるい
            self.statusBar().showMessage(refused or f"{action}しました", 6000)
            self._refresh(force=True)  # 押した結果は次の描き直しで出る（画面は常に導出）

        return run

    def _open_job(self, job_id: str) -> None:
        self._selected_job = job_id
        self._switch(_PAGES.index("詳細"))

    def _refresh(self, force: bool = False) -> None:
        now = datetime.now(timezone.utc)
        jobs = self._source.standing_jobs()
        events = self._source.recent_events()
        stamp = (len(jobs), len(events), self._selected_job, self._stack.currentIndex())
        if not force and stamp == self._stamp:
            return
        self._stamp = stamp

        # 判定は surface の1箇所から読む——画面は何が赤かを決めない（掟: Alert の出口は1本）
        morning = morning_sections(surface(self._source, now, VIEWER))
        count = morning_count(morning)
        self._badge.setText(str(count))
        self._badge.setVisible(count > 0)
        self._morning.populate(
            f"今日あなたが対応するのは {count}件です。ほかは表示していません。",
            morning,
            "対応が必要なものはありません。",
        )
        every = self._source.all_jobs()
        states, definitions, assignees = search_options(every)
        for bar in (self._outlook_filters, self._history_filters):
            bar.set_options(states, definitions, assignees)
        self._search.set_options(states, definitions, assignees)

        self._outlook.populate(
            "実線は作成済みのタスク。点線は業務ルールから予測される、まだ作成されていないタスクです。",
            outlook_sections(
                jobs,
                self._source.enacted_definitions(),
                self._source.origin_keys(),
                now,
                self._outlook_filters.criteria(),
            ),
            "条件に合う予定はありません。",
        )
        self._history.populate(
            "これまでの操作と結果です。行を選ぶと詳細が開きます。",
            history_sections(
                events,
                self._history_filters.criteria(),
                {job.core.job_id: job for job in every},
            ),
            "条件に合う履歴はありません。",
        )
        self._search.populate(
            search_sections(every, self._search.criteria(), {}),
            "条件に合うタスクはありません。",
        )

        if self._selected_job:
            found = next((j for j in every if j.core.job_id == self._selected_job), None)
            if found is not None:
                self._job_page.populate(
                    job_sheet(found, self._source.events_for(self._selected_job))
                )
            else:
                self._job_page.populate(None)
        else:
            self._job_page.populate(None)


def run(source: SheetSource, on_action: Callable[[str, str], str | None]) -> int:
    app = QApplication([])
    app.setStyleSheet(QSS)
    window = MainWindow(source, on_action)
    window.show()
    return app.exec()
