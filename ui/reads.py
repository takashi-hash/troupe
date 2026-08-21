"""参照専用の読み口 — 画面が要るものだけを宣言する（実装は adapters が構造的に満たし、
組み立ての根（main.py）が繋ぐ。ui は adapters を import しない——依存は内向きのみ）。"""

from __future__ import annotations

from typing import Protocol

from domain.definition import Definition
from domain.event import Event
from domain.job import Job


class SheetSource(Protocol):
    """枚の材料の口 — 4枚が要る読みだけ。書く口は無い——画面は常に導出。"""

    def standing_jobs(self) -> tuple[Job, ...]:
        """立っているタスク"""
        ...

    def all_jobs(self) -> tuple[Job, ...]:
        """すべてのタスク"""
        ...

    def enacted_definitions(self) -> tuple[Definition, ...]:
        """有効な業務ルールたち"""
        ...

    def events_for(self, job_id: str) -> tuple[Event, ...]:
        """そのタスクの出来事"""
        ...

    def recent_events(self, limit: int = 200) -> tuple[Event, ...]:
        """近ごろの出来事"""
        ...

    def origin_keys(self) -> frozenset[str]:
        """作成元の鍵たち"""
        ...
