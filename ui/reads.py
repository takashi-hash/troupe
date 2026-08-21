"""参照専用の読み口 — 画面が要るものだけを宣言する（実装は adapters が構造的に満たし、
組み立ての根（main.py）が繋ぐ。ui は adapters を import しない——依存は内向きのみ）。"""

from __future__ import annotations

from typing import Protocol

from domain.definition import Definition
from domain.event import Event
from domain.job import Job


class SheetSource(Protocol):
    """4枚の材料の読み口。書く口は無い——画面は常に導出。"""

    def standing_jobs(self) -> tuple[Job, ...]: ...

    def all_jobs(self) -> tuple[Job, ...]: ...

    def enacted_definitions(self) -> tuple[Definition, ...]: ...

    def events_for(self, job_id: str) -> tuple[Event, ...]: ...

    def recent_events(self, limit: int = 200) -> tuple[Event, ...]: ...

    def origin_keys(self) -> frozenset[str]: ...
