from __future__ import annotations
from app.dto.search_row import SearchRow
from html import escape
from ui.web.frame import _状態

def _検索(rows: tuple[SearchRow, ...], keyword: str) -> str:
    行 = "".join(
        f"<tr><td><a class='id' href='/detail?id={escape(r.id)}'>{escape(r.id)}</a></td>"
        f"<td>{escape(r.head)}</td><td>{escape(r.period or '')}</td>"
        f"<td>{_状態(r.state_name)}</td><td>{escape(r.due)}</td>"
        f"<td>{escape(r.assignee_name or '')}</td></tr>"
        for r in rows
    )
    return (
        "<form method='get' action='/search'>"
        f"<input type='text' name='keyword' value='{escape(keyword)}' "
        "placeholder='keyword'> <button>Search</button></form>"
        "<div class='wrap'><table><tr><th>Id</th><th>Title</th><th>Period</th>"
        "<th>State</th><th>Due date</th><th>Assignee</th></tr>" + 行 + "</table></div>"
    )


