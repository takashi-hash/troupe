"""止める — その版で仕事を生すのをやめると決める。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」・仕事とは何か §4「業務ルールが持つもの」。
| 止める | `deactivate` | その版で仕事を生すのを**やめる**と決める。有効な版の番号が空に戻る——**版の列はそのまま**（積むだけ） |

**人しか起こせない**（I7——`by` の型が `Human`）。
止まった業務ルールからは時計の `create` が仕事を作らない
（`ActiveRuleReader` は有効な版だけを読む——ここは何も足さない）。
"""

from __future__ import annotations

from datetime import datetime

from domain.aggregates.rule.rule import Rule, fields_of
from domain.events.rule.rule_deactivated import RuleDeactivated
from domain.value_objects.people.human import Human


def deactivate(rule: Rule, by: Human, now: datetime) -> tuple[Rule, RuleDeactivated]:
    """有効な版の番号を空に戻す。返るのは（止まった姿, 出来事）の対——I2 と同じ門を通る。"""
    if rule.active is None:
        raise ValueError("もう止まっています")
    stopped_version = rule.active
    data = fields_of(rule) | {"active": None, "activated_by": None, "activated_at": None}
    stopped = Rule.model_validate(data)
    return stopped, RuleDeactivated(
        at=now, by=by, rule_name=rule.name, version=stopped_version
    )
