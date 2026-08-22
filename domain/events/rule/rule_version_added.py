"""版が足された — 業務ルールに新しい版が積まれた、その出来事。

設計: 設計/仕事が回る筋道.md §5。
| 版が足された | どの版か | `RuleVersionAdded` |

**過去形。観察だけ。積むだけ。** 誰が・いつは共通が持つ——
足して残るのは「どの業務ルールの、どの版か」。版の中身は集約が持ち、出来事は番号で指す。
"""

from __future__ import annotations

from domain.events.event import Event
from domain.value_objects.rule.rule_name import RuleName


class RuleVersionAdded(Event):
    """版が足された。版は積むだけ——減った・書き換わったという出来事は無い。"""

    #: どの業務ルールか。
    rule_name: RuleName

    #: どの版か — 積まれた版の番号。
    version: int
