"""題材のデータ — 版の初期値を読む実装。

設計: 設計/どう作るか.md §4・§5。
| **adapters** | **業務の規則** | 帳簿の実装・Port の実装・**腐敗防止層** |
| `custom/<題材>/` | 題材のデータ。**コードにしない** |

`custom/<業務ルールの名>/topic.json` を読み、写すものの束（`Copied`）に組んで返す。
欄の名は版の欄（`VersionForm`）と同じ——instruction・source・required_terms・
description・cycle・days・budget_calls・budget_seconds・owner・max_retries。

無ければ None。**壊れた JSON も None**——読めない題材は初期値なしと同じで、
人がぜんぶ書けば版は積める。ここで止めると、題材の傷が版積みを止めてしまう。
"""

from __future__ import annotations

import json
from pathlib import Path

from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.people.human import Human
from domain.value_objects.people.owner import Owner
from domain.value_objects.rule.budget import Budget
from domain.value_objects.rule.copied import Copied
from domain.value_objects.rule.criteria import AcceptanceCriteria
from domain.value_objects.rule.instruction import Instruction
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source


class FolderTopic:
    """題材の実装 — 題材のフォルダから topic.json を読む。読めない題材は無いのと同じ。"""

    def __init__(self, root: Path = Path("custom")) -> None:
        self._root = root

    def read(self, rule: RuleName) -> Copied | None:
        """題材のデータを初期値として読む。無ければ・読めなければ None。"""
        path = self._root / rule.text / "topic.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        terms = data.get("required_terms")
        if not isinstance(terms, list):
            return None
        try:
            return Copied(
                instruction=Instruction(text=data["instruction"]),
                criteria=AcceptanceCriteria(
                    required_terms=tuple(terms),
                    description=data.get("description", ""),
                ),
                cycle=Cycle(data["cycle"]),
                owner=Owner(person=Human(name=data["owner"])),
                budget=Budget(calls=data["budget_calls"], seconds=data["budget_seconds"]),
                source=Source(location=data["source"]),
                max_retries=data["max_retries"],
                days=data["days"],
            )
        except (KeyError, TypeError, ValueError):
            return None
