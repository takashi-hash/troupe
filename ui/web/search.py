"""検索 — あの仕事はどこ？（人に見えるもの §1）

終わったものも含めて引く（F1）。絞り込みの条件は `RowFilter` の欄そのまま
——キーワード・状態・業務ルール・担当。**器が隠していた絞りを全部出す**。
状態の語→識別子の橋は `gather_search`（筋道 §1）——ここは語を渡すだけ。
"""

from __future__ import annotations

from html import escape

from app.dto.row_filter import RowFilter
from app.dto.search_row import SearchRow
from ui.web.frame import _状態
from ui.words import STATE_GLOSS, 読める


def _検索(rows: tuple[SearchRow, ...], filter: RowFilter) -> str:
    状態の選び = "".join(
        f"<option value='{escape(語)}'"
        + (" selected" if filter.state_label == 語 else "")
        + f">{escape(読める(識別子))}</option>"
        for 語, 識別子 in STATE_GLOSS.items()
    )
    行 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(r.id)}'>{escape(r.id)}</a></td>"
        f"<td>{escape(r.head)}</td><td>{escape(r.period or '')}</td>"
        f"<td>{_状態(r.state_name)}</td><td>{escape(r.due)}</td>"
        f"<td>{escape(r.assignee_name or '')}</td></tr>"
        for r in rows
    )
    found = (f"<p class='page-sub'>{len(rows)} job{'s' if len(rows) != 1 else ''} found"
             " — finished and abandoned ones included.</p>")
    return (
        "<form method='get' action='/search' class='search-form'>"
        f"<input type='text' name='keyword' value='{escape(filter.keyword or '')}' "
        "placeholder='keyword'>"
        f"<select name='state'><option value=''>any state</option>{状態の選び}</select>"
        f"<input type='text' name='rule' value='{escape(filter.rule or '')}' "
        "placeholder='rule name'>"
        f"<input type='text' name='assignee' value='{escape(filter.assignee or '')}' "
        "placeholder='assignee'>"
        "<button class='btn'>Search</button></form>"
        + found
        + "<div class='wrap'><table><tr><th>Id</th><th>Title</th><th>Period</th>"
        "<th>State</th><th>Due date</th><th>Assignee</th></tr>" + 行 + "</table></div>"
    )
