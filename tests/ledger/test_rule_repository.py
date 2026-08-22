"""業務ルールの帳簿の宣言の壊しかた。設計/仕事が回る筋道.md §4・I2。

宣言は Protocol——実装の義務はここで言い切り、実装のテストが同じ検査を通る。
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

from domain.aggregates.rule.rule import Rule
from domain.events.event import Event
from domain.ledger.rule_repository import RuleRepository


def test_書き込みの門は姿と出来事の対しか受けない() -> None:
    """I2 — 出来事なしで版列を書く口が無い。"""
    hints = get_type_hints(RuleRepository.save)
    assert hints["events"] == tuple[Event, ...]
    params = list(inspect.signature(RuleRepository.save).parameters)
    assert params == ["self", "rule", "events"]


def test_読みは鍵で1件だけ() -> None:
    params = list(inspect.signature(RuleRepository.load).parameters)
    assert params == ["self", "name"]
    assert get_type_hints(RuleRepository.load)["return"] == Rule | None
