"""突合 — いま何を作るべきか。

設計: 設計/仕事が回る筋道.md §2「ドメインサービス」・仕事とは何か.md 不変条件 I3・I8。
| いま何を作るべきか | `reconcile` | 有効な版の（識別子・番号・周期・源・**日数**）の列
＋ 既にある作成元の鍵の列 ＋ **予定の定期訪問（患者記号・訪問日）の列** ＋ **いま**。
穴あり版は期間でなく**訪問の接近**（今日JST ≤ 訪問日 ≤ 今日＋日数）で判じる | 業務ルールと仕事の両方をまたぐ |

**唯一のドメインサービス**（集約をまたぐ）。I8（業務ルールが有効なら、
その対象期間——穴あり版はリード内の予定訪問ごと——の仕事が必ず存在する）を時計が回すときの中身。
**穴の無い版**は従来どおり周期といまから `Period` を出す（業務の判断なので app に置けない）。
**穴のある版**は、リード（版の日数）以内に迫った予定の定期訪問ごとに1つ——
比べる「今日」は診療所の暦（JST）。時計は UTC のまま、比較点だけ写す。
既にある鍵は二度作らない（I3）——鍵は `Origin` が出すものと同じ形なので、
同じ中身なら必ず同じ鍵に当たる。
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import date, datetime, timedelta, timezone

from domain.value_objects.calendar.cycle import Cycle
from domain.value_objects.calendar.period import Period
from domain.value_objects.job.origin import Origin
from domain.value_objects.rule.rule_name import RuleName
from domain.value_objects.rule.source import Source

_JST = timezone(timedelta(hours=9))


def reconcile(
    active: Sequence[tuple[RuleName, int, Cycle, Source, int]],
    existing_origin_keys: Collection[str],
    visits: Sequence[tuple[str, str]],
    now: datetime,
) -> tuple[tuple[RuleName, int, Period, str | None, str | None], ...]:
    """作るべき（識別子・番号・対象期間・患者・訪問日）の列。既にある鍵のものは二度出さない。

    穴の無い版の患者・訪問日は空（None）。穴のある版は、リード以内に迫った
    予定の定期訪問ごとに1行——迫った訪問が無ければ1行も出ない（下書きの相手が居ない）。
    訪問仕事の対象期間は訪問日から導く（鍵には入らない——読みのための札）。
    """
    今日 = now.astimezone(_JST).date()
    to_create: list[tuple[RuleName, int, Period, str | None, str | None]] = []
    for rule_name, version_number, cycle, source, days in active:
        if source.has_hole:
            近い訪問: set[tuple[str, str]] = set()
            for 患者, 日 in visits:
                if not 患者.strip():
                    continue  # 患者記号の空な行は数えない——読めない行の扱い
                try:
                    d = date.fromisoformat(日)
                except ValueError:
                    continue
                if 今日 <= d <= 今日 + timedelta(days=days):
                    近い訪問.add((患者, 日))
            for 患者, 日 in sorted(近い訪問):
                if Origin.from_visit(rule_name, 患者, 日).key not in existing_origin_keys:
                    期間 = Period.of(
                        datetime.combine(date.fromisoformat(日), datetime.min.time(), _JST),
                        cycle,
                    )
                    to_create.append((rule_name, version_number, 期間, 患者, 日))
        else:
            period = Period.of(now, cycle)
            if Origin.from_rule(rule_name, version_number, period).key not in existing_origin_keys:
                to_create.append((rule_name, version_number, period, None, None))
    return tuple(to_create)
