"""今日の材料の読みの壊しかた。設計/仕事が回る筋道.md §4——返すのは domain の値。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from app.ports.today_reader import TodayReader
from domain.value_objects.job.today_material import TodayMaterial


def test_読みは全件で_返すのは今日の材料() -> None:
    """宣言が app でも返す型が domain の値なら依存は内向き。"""
    hints = get_type_hints(TodayReader.read_all)
    assert hints["return"] == tuple[TodayMaterial, ...]
    assert list(inspect.signature(TodayReader.read_all).parameters) == ["self"]
