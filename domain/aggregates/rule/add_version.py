"""版を積む — 業務ルールに新しい版を足す。無ければ業務ルールごと生まれる。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」・不変条件 I2。
| 版を積む | `add_version` | **題材のデータを初期値として読み、人が上書きした値**で版を積む |

**版は積むだけ**（I2）——番号は最後の版＋1でなければ赤。減らす道・書き換える道は無い。
人が始めるものなので `by` の型が `Human`——AI がこの手を呼ぶ行は型検査が赤にする。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.rule.rule import Rule, fields_of
from domain.events.rule.rule_version_added import RuleVersionAdded
from domain.values.people.human import Human
from domain.values.rule.rule_name import RuleName
from domain.values.rule.version import Version


def add_version(
    rule: Rule | None, name: RuleName, version: Version, by: Human, now: datetime
) -> tuple[Rule, RuleVersionAdded]:
    """版を積む。返るのは（次の姿, 版が足された）の対——出来事なしで姿を書く形が書けない。

    `rule` が None なら、1版目として業務ルールごと生まれる。
    """
    if rule is not None and rule.name != name:
        raise ValueError("別の名の業務ルールに版は積めません")
    last = 0 if rule is None else rule.versions[-1].number
    if version.number != last + 1:
        raise ValueError(
            f"版の番号は最後の版＋1です（I2: 版は積むだけ）。いまは {last}、来たのは {version.number}"
        )
    if rule is None:
        next_rule = Rule(
            name=name, versions=(version,), active=None, activated_by=None, activated_at=None
        )
    else:
        next_rule = Rule.model_validate(fields_of(rule) | {"versions": (*rule.versions, version)})
    return next_rule, RuleVersionAdded(at=now, by=by, rule_name=name, version=version.number)
