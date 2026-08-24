"""有効な版の読み。

設計: 設計/仕事が回る筋道.md §4・§2「ドメインサービス」。
| `ActiveRuleReader` | Reader | 有効な版の（識別子・番号・周期・源）を読む——`reconcile` の材料と同じ形
| **app** | adapters | `create`・`audit`・`gather_schedule` |

**Reader の返す型は渡す先で決まる**——渡る先は domain の `reconcile` なので domain の値。
`reconcile` の材料と同じ形——詰め替えなしでそのまま渡る。
源も運ぶのは、**穴（`{患者}`）の有無で展開が変わる**から（筋道 §1 `create`）。
"""

from __future__ import annotations

from typing import Protocol

from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source


class ActiveRuleReader(Protocol):
    def read_all(self) -> tuple[tuple[RuleName, int, Cycle, Source], ...]:
        """有効な版の（識別子・番号・周期・源）の列。有効な版の無い業務ルールは出ない。"""
        ...
