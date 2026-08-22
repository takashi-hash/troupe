"""業務ルールの帳簿 — 集約ルートを鍵で1件。**書き込みの門。**

設計: 設計/仕事が回る筋道.md §4（interface の正本）・不変条件 I2。
| `RuleRepository` | Repository | 業務ルールの集約ルートを鍵で1件 | domain | adapters | `create`・`add_version`・`activate`（**`run_check` は仕事が写した基準を見る**） |

**積むのは（次の姿, 出来事の列）の対だけ**——出来事なしで状態を書く口が無い。
版の列は積むだけ（I2）——消した姿・飛ばした姿は型が作らせず、
書き込みの門は前の版列と突き合わせる。
楽観ロックは adapters の中に隠す——業務の語ではない。
"""

from __future__ import annotations

from typing import Protocol

from domain.aggregates.rule.rule import Rule
from domain.events.event import Event
from domain.value_objects.rule.rule_name import RuleName


class RuleRepository(Protocol):
    """帳簿の宣言。実装は adapters、注ぐのは main.py だけ。"""

    def load(self, name: RuleName) -> Rule | None:
        """鍵で1件。無ければ None。返すのは集約ルートだけ。"""
        ...

    def save(self, rule: Rule, events: tuple[Event, ...]) -> None:
        """書き込みの門 — 姿と出来事を**一緒に**積む（I2）。出来事が空なら拒む。"""
        ...
