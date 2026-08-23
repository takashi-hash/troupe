"""検索 — あの仕事はどこ？（人に見えるもの §1）

終わったものも含めて引く（F1）。絞り込みの条件は `RowFilter` の欄そのまま
——キーワード・状態・業務ルール・担当。**器が隠していた絞りを全部出す**。
状態の語→識別子の橋は `gather_search`（筋道 §1）——ここは語を渡すだけ。

帳簿のもう1つの面（/activity と対）——日付の列は等幅、状態はチップ。
"""

from __future__ import annotations

from html import escape

from app.dto.row_filter import RowFilter
from app.dto.search_row import SearchRow
from ui.web.frame import _状態
from ui.words import STATE_GLOSS, 読める

#: 表の小さな整えはこの頁だけのもの——枠の1枚（style.py）に足さず、頁が持って出る。
_様式 = """<style>
/* 仕事の表 — 4pxの目で詰め、見出しは読み幅で折る。日付は .cell-when(等幅)が持つ */
.search-jobs td { padding: 8px 12px; }
.search-jobs .search-title { max-width: 48ch; }
</style>"""


def _検索(rows: tuple[SearchRow, ...], filter: RowFilter) -> str:
    状態の選び = "".join(
        f"<option value='{escape(語)}'"
        + (" selected" if filter.state_label == 語 else "")
        + f">{escape(読める(識別子))}</option>"
        for 語, 識別子 in STATE_GLOSS.items()
    )
    行 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(r.id)}'>{escape(r.id)}</a></td>"
        f"<td class='search-title'>{escape(r.head)}</td>"
        f"<td class='cell-when'>{escape(r.period or '')}</td>"
        f"<td>{_状態(r.state_name)}</td><td class='cell-when'>{escape(r.due)}</td>"
        f"<td>{escape(r.assignee_name or '')}</td></tr>"
        for r in rows
    )
    # 頭は頁の決まり（style.py §2）——数を先に言う。旧 page-sub の言い分は脇に移した
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Ledger</h1>"
        f"<span class='count-pill'><strong>{len(rows)}</strong> jobs found</span>"
        "<span class='page-head__aside'>finished and abandoned ones included"
        "</span></div>"
        "<div class='filter-chips'>"
        "<a class='filter-chip' href='/activity'>Events</a>"
        "<span class='filter-chip is-on' aria-current='true'>Jobs</span></div>"
    )
    # 空の言葉は本当のことを——絞って空か、そもそもまだ仕事が無いかで言い分ける
    if rows:
        表 = (
            "<div class='wrap search-jobs'><table><tr><th>Id</th><th>Title</th>"
            "<th>Period</th><th>State</th><th>Due date</th><th>Assignee</th></tr>"
            + 行 + "</table></div>"
        )
    elif any((filter.keyword, filter.state_label, filter.rule, filter.assignee)):
        表 = ("<p class='empty'>No jobs match these filters. Finished and abandoned "
              "jobs are searchable too — try clearing a field.</p>")
    else:
        表 = ("<p class='empty'>No jobs yet — a job appears here the first time "
              "an active rule reaches its period.</p>")
    return (
        頭
        + _様式
        + "<form method='get' action='/search' class='search-form'>"
        f"<input type='text' name='keyword' value='{escape(filter.keyword or '')}' "
        "placeholder='keyword'>"
        f"<select name='state'><option value=''>any state</option>{状態の選び}</select>"
        f"<input type='text' name='rule' value='{escape(filter.rule or '')}' "
        "placeholder='rule name'>"
        f"<input type='text' name='assignee' value='{escape(filter.assignee or '')}' "
        "placeholder='assignee'>"
        "<button class='btn'>Search</button></form>"
        + 表
    )
