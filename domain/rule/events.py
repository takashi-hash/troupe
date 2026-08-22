"""業務ルールの集約のドメインイベント。

設計: 設計/仕事が回る筋道.md §5（正本）。
"""

from __future__ import annotations

from typing import Literal

from domain.rule.values import RuleName
from domain.shared import Event, Human

class RuleVersionAdded(Event):
    """版が足された — どの版か。"""

    name: Literal["RuleVersionAdded"] = "RuleVersionAdded"
    rule: RuleName
    version: int


class RuleActivated(Event):
    """業務ルールが有効になった — 誰が・どの版か。**人が主語。**"""

    name: Literal["RuleActivated"] = "RuleActivated"
    rule: RuleName
    version: int
    activated_by: Human
