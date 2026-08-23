from __future__ import annotations
from app.dto.history_row import HistoryRow
from html import escape
from ui.words import 出来事
from ui.words import 起こす者

def _履歴(rows: tuple[HistoryRow, ...]) -> str:
    行 = "".join(
        f"<tr><td>{escape(r.at)}</td><td>{escape(起こす者(r.by))}</td><td>{escape(出来事(r.what))}</td>"
        f"<td><a class='id' href='/detail?id={escape(r.job_id)}'>{escape(r.head)}</a></td></tr>"
        for r in rows
    )
    return (
        "<div class='wrap'><table><tr><th>When</th><th>Who</th><th>What happened</th>"
        "<th>Job</th></tr>" + 行 + "</table></div>"
    )


