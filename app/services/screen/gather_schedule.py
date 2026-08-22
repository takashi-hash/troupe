"""予定を集める — 先に何が来る？

設計: 設計/人に見えるもの.md §1「予定」・§2「予定の行」・§3。

**判定するのは仕様（reconcile・rule_allowed）。集めて渡すだけ。帳簿に書かない。**
次の対象期間は業務ルール×暦から導き、その仕事が**まだ無ければ（未作成）**と添える。
有効にしていない業務ルールに次の対象期間は無い（決め済み）。
押せることは仕様（`rule_allowed`）に尋ねる——ここで if を組まない。
"""

from __future__ import annotations

from app.dto.schedule_row import ScheduleRow
from app.ports.active_rule_reader import ActiveRuleReader
from app.ports.clock_port import ClockPort
from app.ports.origin_reader import OriginReader
from app.ports.rule_reader import RuleReader
from domain.services.reconcile import reconcile
from domain.services.rule_allowed import rule_allowed
from domain.value_objects.calendar.period import Period


def gather_schedule(
    rules: RuleReader,
    active: ActiveRuleReader,
    origins: OriginReader,
    clock: ClockPort,
) -> tuple[ScheduleRow, ...]:
    """業務ルールの一覧を予定の行にして返す。読むだけ。"""
    now = clock.now()
    未作成 = {
        (name.text, number): period.text
        for name, number, period in reconcile(active.read_all(), origins.keys(), now)
    }
    次の期間: dict[str, str] = {}
    for name, _number, cycle in active.read_all():
        次の期間[name.text] = Period.of(now, cycle).text

    rows: list[ScheduleRow] = []
    for line in rules.read_all():
        next_period: str | None = None
        if line.active_version is not None:
            base = 次の期間.get(line.name)
            if base is not None:
                済み = (line.name, line.active_version) not in 未作成
                next_period = base + ("（作られた）" if 済み else "（未作成）")
        actions = rule_allowed(line.active_version)
        rows.append(
            ScheduleRow(
                rule=line.name,
                instruction=line.instruction,
                version=line.version_number,
                active_version=line.active_version,
                next_period=next_period,
                actions=actions,
            )
        )
    return tuple(rows)
