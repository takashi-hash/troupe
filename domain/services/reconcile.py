"""突合 — いま何を作るべきか。

設計: 設計/仕事が回る筋道.md §2「ドメインサービス」・仕事とは何か.md 不変条件 I3・I8。
| いま何を作るべきか | `reconcile` | 有効な版の識別子と番号の列 ＋ 既にある作成元の鍵の列
＋ 周期 ＋ **いま** | 業務ルールと仕事の両方をまたぐ |

**唯一のドメインサービス**（集約をまたぐ）。I8（業務ルールが有効なら、
その対象期間の仕事が必ず存在する）を時計が回すときの中身。
**`reconcile` が対象期間も決める。** 周期といまから `Period` を出す——
これは業務の判断なので app に置けない。
既にある鍵は二度作らない（I3）——鍵は `Origin` が出すものと同じ形なので、
同じ中身なら必ず同じ鍵に当たる。
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime

from domain.values.calendar.cycle import Cycle
from domain.values.calendar.period import Period
from domain.values.job.origin import Origin
from domain.values.rule.rule_name import RuleName


def reconcile(
    active: Sequence[tuple[RuleName, int, Cycle]],
    existing_origin_keys: Collection[str],
    now: datetime,
) -> tuple[tuple[RuleName, int, Period], ...]:
    """作るべき（識別子・番号・対象期間）の列。既にある鍵のものは二度出さない。"""
    to_create: list[tuple[RuleName, int, Period]] = []
    for rule_name, version_number, cycle in active:
        period = Period.of(now, cycle)
        if Origin.from_rule(rule_name, version_number, period).key not in existing_origin_keys:
            to_create.append((rule_name, version_number, period))
    return tuple(to_create)
