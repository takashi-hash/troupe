"""突合 — いま何を作るべきか。

設計: 設計/仕事が回る筋道.md §2「ドメインサービス」・仕事とは何か.md 不変条件 I3・I8。
| いま何を作るべきか | `reconcile` | 有効な版の（識別子・番号・周期・**源**）の列 ＋ 既にある作成元の鍵の列
＋ **予定の訪問（患者記号・訪問日の文字）の列** ＋ **いま** | 業務ルールと仕事の両方をまたぐ |

**唯一のドメインサービス**（集約をまたぐ）。I8（業務ルールが有効なら、
その対象期間の仕事が必ず存在する）を時計が回すときの中身。
**`reconcile` が対象期間も決める。** 周期といまから `Period` を出す——
これは業務の判断なので app に置けない。
**源に `{患者}` の穴を持つ版は、対象期間に予定の訪問がある患者ごとに1つ**（筋道 §1 `create`）
——期間内かを判じるのもここ（業務の判断）。
既にある鍵は二度作らない（I3）——鍵は `Origin` が出すものと同じ形なので、
同じ中身なら必ず同じ鍵に当たる。
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime

from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.origin import Origin
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source


def reconcile(
    active: Sequence[tuple[RuleName, int, Cycle, Source]],
    existing_origin_keys: Collection[str],
    visits: Sequence[tuple[str, str]],
    now: datetime,
) -> tuple[tuple[RuleName, int, Period, str | None], ...]:
    """作るべき（識別子・番号・対象期間・患者）の列。既にある鍵のものは二度出さない。

    穴の無い版の患者は空（None）。穴のある版は、対象期間に予定の訪問がある
    患者ごとに1行——予定が無ければ1行も出ない（下書きの相手が居ない）。
    """
    to_create: list[tuple[RuleName, int, Period, str | None]] = []
    for rule_name, version_number, cycle, source in active:
        period = Period.of(now, cycle)
        patients: tuple[str | None, ...] = (
            # 患者記号の空な行は数えない——読めない日付と同じ「読めない行」の扱い
            tuple(sorted({患者 for 患者, 日 in visits if 患者.strip() and period.covers(日)}))
            if source.has_hole
            else (None,)
        )
        for patient in patients:
            if (
                Origin.from_rule(rule_name, version_number, period, patient).key
                not in existing_origin_keys
            ):
                to_create.append((rule_name, version_number, period, patient))
    return tuple(to_create)
