"""予定（Automations）— 業務ルールと、いま流れている仕事（人に見えるもの §1）

routes.py の page-sub がこの上に載る——ここでは言い直さない。
やること（instruction）は長文——読み幅で折る。版の数字は右に揃えて等幅。
"""

from __future__ import annotations

from html import escape

from app.dto.schedule_row import ScheduleRow
from app.dto.search_row import SearchRow
from ui.web.frame import _状態
from ui.words import 語

#: 表の小さな整えはこの頁だけのもの——枠の1枚（style.py）に足さず、頁が持って出る。
_様式 = """<style>
/* 予定の表 — 4pxの目で詰める。やることは読み幅で折り、版の数字は右に揃える。
   日付は .cell-when(等幅)が持ち、折らない */
.automations-rules td, .automations-jobs td { padding: 8px 12px; }
.automations-instr { max-width: 64ch; }
.automations-ver { text-align: right; }
.automations-name { white-space: nowrap; }
</style>"""


def _予定(rules: tuple[ScheduleRow, ...], jobs: tuple[SearchRow, ...]) -> str:
    決まり = "".join(
        f"<tr><td class='mono automations-name'>{escape(r.rule)}</td>"
        f"<td class='automations-instr'>{escape(r.instruction)}</td>"
        f"<td class='automations-ver'>{r.version}</td>"
        f"<td class='automations-ver'>{r.active_version if r.active_version else '—'}</td>"
        # 次の対象期間だけを出す。**その期間の仕事が在るかは、すぐ下の表が示す**
        # ——同じことを2箇所で言わない（言い換えを画面で作らない）
        f"<td class='cell-when'>{escape((r.next_period or '—').split('（')[0])}</td></tr>"
        for r in rules
    )
    仕事 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(j.id)}'>{escape(j.id)}</a></td>"
        f"<td class='automations-instr'>{escape(j.head)}</td>"
        f"<td class='cell-when'>{escape(j.period or '')}</td>"
        f"<td>{_状態(j.state_name)}</td><td class='cell-when'>{escape(j.due)}</td></tr>"
        for j in jobs
    )
    # 頭は頁の決まり（style.py §2）——数を先に言う。routes.py の page-sub の下に載る
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Automations</h1>"
        f"<span class='count-pill'><strong>{len(rules)}</strong> rules</span>"
        f"<span class='page-head__aside num'>{len(jobs)} jobs in flight</span></div>"
    )
    # 空の言葉は本当のことを——表の頭だけ残さず、言葉に置き換える
    決まりの表 = (
        (
            "<div class='wrap automations-rules'><table>"
            "<tr><th>Rule</th><th>Instruction</th>"
            "<th class='automations-ver'>Version</th>"
            "<th class='automations-ver'>Active version</th>"
            "<th>Next period</th></tr>" + 決まり + "</table></div>"
        )
        if rules
        else "<p class='empty'>No rules registered — nothing runs until a rule "
             "is written and activated.</p>"
    )
    仕事の表 = (
        (
            "<div class='wrap automations-jobs'><table>"
            "<tr><th>Id</th><th>Title</th><th>Period</th><th>State</th>"
            "<th>Due date</th></tr>" + 仕事 + "</table></div>"
        )
        if jobs
        else "<p class='empty'>No jobs in flight — a job opens when an active rule "
             "reaches its next period, and leaves this list when it is finished "
             "or abandoned.</p>"
    )
    return (
        頭
        + _様式
        + f"<h3 class='section-title'>{語('業務ルール')}</h3>"
        + 決まりの表
        + "<h3 class='section-title'>Jobs in flight</h3>"
        + 仕事の表
    )
