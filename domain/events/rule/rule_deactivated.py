"""業務ルールが止められた — その版で仕事を生すのをやめると人が決めた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| **業務ルールが止められた** | どの版を止めたか | `RuleDeactivated` |

**人が主語**——有効化の逆も判断（公理 I7 の6つのひとつ）。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.value_objects.people.human import Human
from domain.value_objects.rule.rule_name import RuleName


class RuleDeactivated(Event):
    """業務ルールが止められた。版の列はそのまま——止まっても歴史は消えない。"""

    #: **人が主語**——太字が型になる。AI や時計がこの手を起こした形は書けない。
    by: Human  # pyright: ignore[reportIncompatibleVariableOverride]

    #: どの業務ルールの、どの版を止めたか。
    rule_name: RuleName
    version: int
