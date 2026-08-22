"""業務ルールが有効になった — その版で仕事を生してよいと人が決めた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| **業務ルールが有効になった** | 誰が・どの版か | `RuleActivated` |

**人が主語。** 誰が・いつは共通が持つ——足して残るのは「どの業務ルールの、どの版か」。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.values.people.human import Human
from domain.values.rule.rule_name import RuleName


class RuleActivated(Event):
    """業務ルールが有効になった。「判断は人間」の実物のひとつ。"""

    #: **人が主語**——太字が型になる。AI や時計がこの手を起こした形は書けない。
    by: Human  # pyright: ignore[reportIncompatibleVariableOverride]

    #: どの業務ルールか。
    rule_name: RuleName

    #: どの版か — 有効になった版の番号。
    version: int
