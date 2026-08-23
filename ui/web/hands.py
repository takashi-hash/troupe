from __future__ import annotations

from __future__ import annotations

from collections.abc import Callable
from html import escape
from urllib.parse import quote
from typing import Any, NamedTuple, Protocol

from app.dto.detail_view import DetailView
from app.dto.history_row import HistoryRow
from app.dto.row_filter import RowFilter
from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from app.dto.patient_row import PatientRow
from app.dto.pattern_row import PatternRow
from app.dto.visit_view import VisitView
from app.services.screen.gather_route import _km
from app.dto.route_stop import RouteStop
from app.dto.patient_view import PatientView
from app.dto.today_row import TodayRow
from ui.words import 出来事, 操作, 状態, 語, 起こす者, 読める

class 読む手(Protocol):
    def __call__(self) -> tuple[TodayRow, ...]: ...


class 押す手(Protocol):
    def __call__(self, what: str, id: str, text: str) -> str | None:
        """通れば None、断られたら理由の文字。"""
        ...


class 詳細の手(Protocol):
    def __call__(self, id: str) -> DetailView | None: ...


class 予定の手(Protocol):
    def __call__(self) -> tuple[ScheduleRow, ...]: ...


class 決まりを押す手(Protocol):
    def __call__(
        self, what: str, name: str, version: int, fields: dict[str, str]
    ) -> str | None: ...


class 履歴の手(Protocol):
    def __call__(self) -> tuple[HistoryRow, ...]: ...


class 検索の手(Protocol):
    def __call__(self, filter: RowFilter) -> tuple[SearchRow, ...]: ...


class 頼む手(Protocol):
    def __call__(self, body: str, fields: dict[str, str]) -> str | None: ...


class 来ている仕事の手(Protocol):
    def __call__(self) -> tuple[SearchRow, ...]: ...


class 患者たちの手(Protocol):
    def __call__(self) -> tuple[PatientRow, ...]: ...


class 患者の手(Protocol):
    def __call__(self, code: str) -> PatientView | None: ...


class 取り決めの手(Protocol):
    def __call__(self) -> tuple[PatternRow, ...]: ...


class 取り決めを押す手(Protocol):
    def __call__(self, what: str, fields: dict[str, str]) -> str | None: ...


class 今日の手(Protocol):
    def __call__(self) -> str: ...


class 訪問の手(Protocol):
    def __call__(self, id: str) -> VisitView | None: ...


class 訪問を押す手(Protocol):
    def __call__(self, what: str, fields: dict[str, str]) -> str | None: ...


class 道順の手(Protocol):
    def __call__(
        self, day: str
    ) -> tuple[tuple[float, float] | None, dict[str, tuple[RouteStop, ...]]]: ...


class 手(NamedTuple):
    """器に注がれる手。**中身は知らない**——読む・押す、それだけ。

    机の窓は同じ手を1つずつ受け取る。web は1回ごとに束で受け取り、
    使い終わったら `close` で閉じる。

    **欄の名は机の窓の口と同じ**——同じ手が、どちらの器にも注げる。
    （形をここに写すのは、web の器が机の道具を読み込まないため。
    ずれたら組み立ての根が型で赤くなる——注ぐのは main.py だけだから。）
    """

    fetch: 読む手
    act: 押す手
    detail: 詳細の手
    schedule_fetch: 予定の手
    schedule_act: 決まりを押す手
    history_fetch: 履歴の手
    search: 検索の手
    request: 頼む手
    upcoming: 来ている仕事の手
    patients: 患者たちの手
    patient: 患者の手
    patterns: 取り決めの手
    pattern_act: 取り決めを押す手
    visit: 訪問の手
    visit_act: 訪問を押す手
    route: 道順の手
    today: 今日の手
    close: Callable[[], None]


class 手を開く(Protocol):
    def __call__(self) -> 手:
        """帳簿を開き、手の束を組んで返す。**呼ばれるたびに新しい。**"""
        ...


