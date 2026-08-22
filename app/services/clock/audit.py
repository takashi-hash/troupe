"""突き合わせる — 時計が始めるもの。

設計: 設計/仕事が回る筋道.md §1・不変条件 I8。
| 突き合わせる | `audit` | 有効な版に対して、いまの対象期間の仕事が在るかを数え合わせる（**I8 の周期で回る突合**） | **読むだけ**。書かない |

**即時があることは、結果を要らなくしない。** `create` が作るのは道の上の話——
この突合は**帳簿そのもの**を数え合わせる。帳簿は道具より長生きする。
"""

from __future__ import annotations

from app.ports.active_rule_reader import ActiveRuleReader
from app.ports.clock_port import ClockPort
from app.ports.origin_reader import OriginReader
from domain.services.reconcile import reconcile
from domain.value_objects.calendar.period import Period
from domain.value_objects.rule.rule_name import RuleName


def audit(
    active_rules: ActiveRuleReader, origins: OriginReader, clock: ClockPort
) -> tuple[tuple[RuleName, int, Period], ...]:
    """有効なのに仕事の無い（識別子・版・対象期間）の列。空なら I8 は守られている。"""
    return reconcile(active_rules.read_all(), origins.keys(), clock.now())
