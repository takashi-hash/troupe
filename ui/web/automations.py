from __future__ import annotations
from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from html import escape
from ui.web.frame import _状態
from ui.words import 語

#: 表の小さな整えはこの頁だけのもの——枠の1枚（style.py）に足さず、頁が持って出る。
_様式 = """<style>
/* 予定の表 — 広い台紙での整え。日付・期間は折らず、やることは読み幅で折る */
.cell-tight { white-space: nowrap; }
.cell-instr { max-width: 64ch; }
</style>"""


def _予定(rules: tuple[ScheduleRow, ...], jobs: tuple[SearchRow, ...]) -> str:
    決まり = "".join(
        f"<tr><td class='mono cell-tight'>{escape(r.rule)}</td>"
        f"<td class='cell-instr'>{escape(r.instruction)}</td>"
        f"<td>{r.version}</td><td>{r.active_version if r.active_version else '—'}</td>"
        # 次の対象期間だけを出す。**その期間の仕事が在るかは、すぐ下の表が示す**
        # ——同じことを2箇所で言わない（言い換えを画面で作らない）
        f"<td class='cell-tight'>{escape((r.next_period or '—').split('（')[0])}</td></tr>"
        for r in rules
    )
    仕事 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(j.id)}'>{escape(j.id)}</a></td>"
        f"<td class='cell-instr'>{escape(j.head)}</td>"
        f"<td class='cell-tight'>{escape(j.period or '')}</td>"
        f"<td>{_状態(j.state_name)}</td><td class='cell-tight'>{escape(j.due)}</td></tr>"
        for j in jobs
    )
    仕事が無い = "" if jobs else "<p class='empty'>No jobs in flight.</p>"
    # 頭は頁の決まり（style.py §2）——数を先に言う。routes.py の page-sub の下に載る
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Automations</h1>"
        f"<span class='count-pill'><strong>{len(rules)}</strong> rules</span>"
        f"<span class='page-head__aside'>{len(jobs)} jobs in flight</span></div>"
    )
    return (
        頭
        + _様式
        + f"<h3 class='section-title'>{語('業務ルール')}</h3><div class='wrap'><table>"
        "<tr><th>Rule</th><th>Instruction</th><th>Version</th><th>Active version</th>"
        "<th>Next period</th></tr>" + 決まり + "</table></div>"
        "<h3 class='section-title'>Jobs in flight</h3><div class='wrap'><table>"
        "<tr><th>Id</th><th>Title</th><th>Period</th><th>State</th><th>Due date</th></tr>"
        + 仕事
        + "</table></div>"
        + 仕事が無い
    )
