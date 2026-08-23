from __future__ import annotations
from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from html import escape
from ui.web.frame import _状態
from ui.words import 語

def _予定(rules: tuple[ScheduleRow, ...], jobs: tuple[SearchRow, ...]) -> str:
    決まり = "".join(
        f"<tr><td>{escape(r.rule)}</td><td>{escape(r.instruction)}</td>"
        f"<td>{r.version}</td><td>{r.active_version if r.active_version else '—'}</td>"
        # 次の対象期間だけを出す。**その期間の仕事が在るかは、すぐ下の表が示す**
        # ——同じことを2箇所で言わない（言い換えを画面で作らない）
        f"<td>{escape((r.next_period or '—').split('（')[0])}</td></tr>"
        for r in rules
    )
    仕事 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(j.id)}'>{escape(j.id)}</a></td>"
        f"<td>{escape(j.head)}</td><td>{escape(j.period or '')}</td>"
        f"<td>{_状態(j.state_name)}</td><td>{escape(j.due)}</td></tr>"
        for j in jobs
    )
    return (
        f"<h3>{語('業務ルール')}</h3><div class='wrap'><table>"
        "<tr><th>Rule</th><th>Instruction</th><th>Version</th><th>Active version</th>"
        "<th>Next period</th></tr>" + 決まり + "</table></div>"
        "<h3>Jobs in flight</h3><div class='wrap'><table>"
        "<tr><th>Id</th><th>Title</th><th>Period</th><th>State</th><th>Due date</th></tr>"
        + 仕事
        + "</table></div>"
    )


