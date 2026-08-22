"""有効にする — その版でいま仕事を生してよい、という人の判断。

設計: 設計/仕事が回る筋道.md §1・仕事とは何か.md §4「業務ルールが持つもの」・不変条件 I7。
| 有効にする | `activate` | その版で仕事を生してよいと決める |
| 有効な版の番号 | **0か1つ**。版2を有効にすると版1は自動で無効になる |

**人しか起こせない**（I7 公理の執行者）——`by` の型が `Human` なので、
AI がこの手を呼ぶ行は型検査が赤にする。型を潜っても、次の姿の欄
`activated_by: Human` が実行時に拒む——AI が有効にした姿がそもそも書けない。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.rule.rule import Rule, fields_of
from domain.events.rule.rule_activated import RuleActivated
from domain.value_objects.people.human import Human


def activate(
    rule: Rule, version: int, by: Human, now: datetime
) -> tuple[Rule, RuleActivated]:
    """有効を渡す。返るのは（次の姿, 業務ルールが有効になった）の対——I1 と同じ形。

    有効な版の番号は0か1つ——番号を差し替えるだけなので、前の版は自動で無効になる。
    """
    if version not in [v.number for v in rule.versions]:
        raise ValueError(f"無い版は有効にできません: {version}")
    data = fields_of(rule) | {"active": version, "activated_by": by, "activated_at": now}
    return Rule.model_validate(data), RuleActivated(
        at=now, by=by, rule_name=rule.name, version=version
    )
