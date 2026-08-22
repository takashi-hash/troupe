"""有効にする — 人が始めるもの。

設計: 設計/仕事が回る筋道.md §1「人が始めるもの」。
| 有効にする | `activate` | その版で仕事を生してよいと決める |

アプリケーションサービスの形はいつも同じ——**読む → domain の操作 → 書く**。
業務の判断はしない——決めるのは人で、ここは運ぶだけ。
無い業務ルール・無い版は**断りに変えるだけ**。
"""

from __future__ import annotations

from app.ports.clock_port import ClockPort
from app.services.refusal import Refusal
from domain.aggregates.rule import activate as 有効化
from domain.repositories.rule_repository import RuleRepository
from domain.value_objects.people.human import Human
from domain.value_objects.rule.rule_name import RuleName


def activate(
    rules: RuleRepository, clock: ClockPort, name: str, version: int, by: str
) -> Refusal | None:
    """通れば None。断られたら理由。エラーは投げない——版の列に傷をつけない。

    **画面から渡るのは文字だけ**（設計 §1）——ui は domain を知らないので、
値に組むのはここ。組めない文字は断りに変わる。
    """
    try:
        鍵, 人 = RuleName(text=name), Human(name=by)
    except ValueError as なぜ:
        return Refusal(reason=str(なぜ))
    rule = rules.load(鍵)
    if rule is None:
        return Refusal(reason="その業務ルールはありません")
    try:
        next_rule, event = 有効化.activate(rule, version, by=人, now=clock.now())
    except ValueError as なぜ:
        return Refusal(reason=str(なぜ))
    rules.save(next_rule, (event,))
    return None
