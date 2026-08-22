"""版を積む — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」・§4。
| 版を積む | `add_version` | **題材のデータを初期値として読み、人が上書きした値**で版を積む |
| `TopicPort` | Port | 題材のデータ（版の中身）を読む | **app** | adapters | `add_version` |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
題材のデータが初期値、人が書いた欄がそれを上書きする。題材に無ければ人がぜんぶ書く。
版の番号は最後の版＋1しかありえない（I2）——数えるだけで、判断ではない。
業務の判断はしない。義務が拒んだら**断りに変えるだけ**。
"""

from __future__ import annotations

from collections.abc import Mapping

from app.ports.clock_port import ClockPort
from app.ports.topic_port import TopicPort
from app.services.refusal import Refusal
from domain.aggregates.rule import add_version as 版積み
from domain.ledger.rule_repository import RuleRepository
from domain.values.people.human import Human
from domain.values.rule.copied import Copied
from domain.values.rule.rule_name import RuleName
from domain.values.rule.version import Version


def add_version(
    rules: RuleRepository,
    topics: TopicPort,
    clock: ClockPort,
    name: RuleName,
    by: Human,
    written: Mapping[str, object],
) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——版の列に傷をつけない。"""
    base = topics.read(name)
    initial: dict[str, object] = (
        {} if base is None else {field: getattr(base, field) for field in Copied.model_fields}
    )
    rule = rules.load(name)
    last = 0 if rule is None else rule.versions[-1].number
    try:
        copied = Copied.model_validate(initial | dict(written))
        version = Version(
            number=last + 1,
            instruction=copied.instruction,
            criteria=copied.criteria,
            cycle=copied.cycle,
            days=copied.days,
            budget=copied.budget,
            owner=copied.owner,
            source=copied.source,
            max_retries=copied.max_retries,
        )
        next_rule, event = 版積み.add_version(rule, name, version, by=by, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=str(なぜ))
    rules.save(next_rule, (event,))
    return None
