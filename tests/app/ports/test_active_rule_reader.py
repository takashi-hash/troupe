"""有効な版の読みの壊しかた。設計/仕事が回る筋道.md §4・§2——`reconcile` の材料と同じ形。"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from app.ports.active_rule_reader import ActiveRuleReader
from domain.values.calendar.cycle import Cycle
from domain.values.rule.rule_name import RuleName


def test_返すのは有効な版の識別子と番号と周期の列() -> None:
    """`reconcile` の材料と同じ形——詰め替えなしでそのまま渡る。"""
    hints = get_type_hints(ActiveRuleReader.read_all)
    assert hints["return"] == tuple[tuple[RuleName, int, Cycle], ...]
    assert list(inspect.signature(ActiveRuleReader.read_all).parameters) == ["self"]
