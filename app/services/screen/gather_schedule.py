"""予定を集める — 先に何が来る？

設計: 設計/人に見えるもの.md §1「予定」・§2「予定の行」・§3。

**判定するのは仕様（reconcile・rule_allowed）。集めて渡すだけ。帳簿に書かない。**
次の対象期間は業務ルール×暦から導き、その仕事が**まだ無ければ（未作成）**と添える。
有効にしていない業務ルールに次の対象期間は無い（決め済み）。
押せることは仕様（`rule_allowed`）に尋ねる——ここで if を組まない。
"""

from __future__ import annotations

from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from app.ports.active_rule_reader import ActiveRuleReader
from app.ports.clock_port import ClockPort
from app.ports.origin_reader import OriginReader
from app.ports.rule_reader import RuleReader
from app.ports.scheduled_visit_reader import ScheduledVisitReader
from app.ports.today_reader import TodayReader
from app.services.screen.gather_history import heading
from domain.aggregates.job.life import STATE_WORDS
from domain.services.reconcile import reconcile
from domain.services.rule_allowed import rule_allowed
from domain.value_objects.calendar.period import Period

_状態の語 = {ident: word for word, ident in STATE_WORDS.items()}


def gather_schedule(
    rules: RuleReader,
    active: ActiveRuleReader,
    origins: OriginReader,
    visits: ScheduledVisitReader,
    clock: ClockPort,
) -> tuple[ScheduleRow, ...]:
    """業務ルールの一覧を予定の行にして返す。読むだけ。"""
    now = clock.now()
    未作成: dict[tuple[str, int], int] = {}
    for name, number, _period, _patient, _visit_date in reconcile(
        active.read_all(), origins.keys(), visits.read_scheduled(), now
    ):
        未作成[(name.text, number)] = 未作成.get((name.text, number), 0) + 1
    次の期間: dict[str, str] = {}
    for name, _number, cycle, _source, _days in active.read_all():
        次の期間[name.text] = Period.of(now, cycle).text

    rows: list[ScheduleRow] = []
    for line in rules.read_all():
        next_period: str | None = None
        if line.active_version is not None:
            base = 次の期間.get(line.name)
            if base is not None:
                残り = 未作成.get((line.name, line.active_version), 0)
                next_period = base + (
                    "（作られた）" if 残り == 0
                    else "（未作成）" if 残り == 1
                    else f"（未作成 {残り}件）"
                )
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


def gather_upcoming(today: TodayReader) -> tuple[SearchRow, ...]:
    """作られた仕事の列（終点以外——一覧の読みが運ぶ範囲そのまま）。予定の下段。

    頼んだ直後の仕事がここに見える——**押して何も起きないのが一番わるい**（§3）。
    """
    return tuple(
        SearchRow(
            id=m.id.text,
            head=heading(
                m.rule.text if m.rule is not None else None,
                m.period.text if m.period is not None else None,
                m.request_head or m.instruction.text,
            ),
            period=m.period.text if m.period is not None else None,
            instruction=m.instruction.text,
            state_name=_状態の語[m.state_name],
            due=m.due.at.isoformat()[:16].replace("T", " "),
            assignee_name=m.assignee_name,
        )
        for m in today.read_all()
    )
