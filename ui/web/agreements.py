from __future__ import annotations
from app.dto.pattern_row import PatternRow
from html import escape
from ui.words import 操作
from urllib.parse import quote

def _取り決めたち(rows: tuple[PatternRow, ...], added: str | None = None) -> str:
    バナー = (f"<div class='banner banner--success'>✓ {escape(added)}</div>" if added else "")
    行 = "".join(
        f"<tr{' class=agreement-row--ended' if r.active_to else ''}>"
        f"<td><a class='patient-chip' href='/patient?code={quote(r.patient)}'>{escape(r.patient)}</a></td>"
        f"<td>{escape(r.weekday)}</td>"
        f"<td>{'every week' if r.every_weeks == '1' else f'every {escape(r.every_weeks)} weeks'}</td>"
        f"<td>{escape(r.clinician)}</td><td>{escape(r.purpose)}</td>"
        f"<td>{escape(r.active_from)}</td>"
        f"<td>{escape(r.active_to) if r.active_to else '—'}</td>"
        f"<td>" + (
            f"<form class='act' method='post' action='/patterns/act'>"
            f"<input type='hidden' name='what' value='end_pattern'>"
            f"<input type='hidden' name='id' value='{escape(r.id)}'>"
            f"<button class='btn btn--destructive btn--small'"
            " onclick=\"return confirm('End this agreement? Its future planned visits will be cancelled.')\">End</button></form>"
            if r.active_to is None else ""
        ) + "</td></tr>"
        for r in rows
    )
    曜日 = "".join(f"<option>{w}</option>" for w in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"))
    form = (
        "<h3>Agree a new recurring visit</h3>"
        "<p class='sub'>The agreement with the patient is the human judgment."
        " Troupe's pulse expands it into the calendar — that part is bookkeeping.</p>"
        "<form class='act' method='post' action='/patterns/act'>"
        "<input type='hidden' name='what' value='add_pattern'>"
        "<input type='text' name='patient' placeholder='P-001' required>"
        f"<select name='weekday'>{曜日}</select>"
        "<input type='text' name='clinician' placeholder='Dr-A' required>"
        "<input type='text' name='purpose' placeholder='weekly home visit' required>"
        "<input type='date' name='start' required>"
        f"<button>{escape(操作('add_pattern'))}</button></form>"
    )
    return (
        "<div class='wrap'><table><tr><th>Patient</th><th>Weekday</th><th>Clinician</th>"
        "<th>Purpose</th><th>From</th><th>To</th><th></th></tr>" + 行 + "</table></div>" + form
    )


