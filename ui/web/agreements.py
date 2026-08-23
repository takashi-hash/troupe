from __future__ import annotations
from app.dto.pattern_row import PatternRow
from html import escape
from ui.words import 操作
from urllib.parse import quote

def _取り決めたち(rows: tuple[PatternRow, ...], added: str | None = None) -> str:
    # 有効＝active_to が無いもの。終わった数は脇に添える
    有効 = sum(1 for r in rows if r.active_to is None)
    終了 = len(rows) - 有効
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Agreements</h1>"
        f"<span class='count-pill'><strong>{有効}</strong> in force</span>"
        + (f"<span class='page-head__aside'>{終了} ended</span>" if 終了 else "")
        + "</div>"
    )
    バナー = (f"<div class='banner banner--success'>✓ {escape(added)}</div>" if added else "")
    行 = "".join(
        f"<tr{' class=agreement-row--ended' if r.active_to else ''}>"
        f"<td><a class='patient-chip' href='/patient?code={quote(r.patient)}'>{escape(r.patient)}</a></td>"
        f"<td>{escape(r.weekday)}</td>"
        f"<td>{'every week' if r.every_weeks == '1' else f'every {escape(r.every_weeks)} weeks'}</td>"
        f"<td>{escape(r.clinician)}</td><td>{escape(r.purpose)}</td>"
        f"<td class='cell-when'>{escape(r.active_from)}</td>"
        f"<td class='cell-when'>{escape(r.active_to) if r.active_to else '—'}</td>"
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
        "<aside class='form-card'>"
        "<h3 class='form-card__title'>Agree a new recurring visit</h3>"
        "<p class='sub'>The agreement with the patient is the human judgment."
        " Troupe's pulse expands it into the calendar — that part is bookkeeping.</p>"
        "<form method='post' action='/patterns/act'>"
        "<input type='hidden' name='what' value='add_pattern'>"
        "<div class='form-grid'>"
        "<div class='field'><label for='agr-patient'>Patient</label>"
        "<input type='text' id='agr-patient' name='patient' placeholder='P-001' required></div>"
        "<div class='field'><label for='agr-weekday'>Weekday</label>"
        f"<select id='agr-weekday' name='weekday'>{曜日}</select></div>"
        "<div class='field'><label for='agr-clinician'>Clinician</label>"
        "<input type='text' id='agr-clinician' name='clinician' placeholder='Dr-A' required></div>"
        "<div class='field'><label for='agr-purpose'>Purpose</label>"
        "<input type='text' id='agr-purpose' name='purpose' placeholder='weekly home visit' required></div>"
        "<div class='field'><label for='agr-start'>Start</label>"
        "<input type='date' id='agr-start' name='start' required></div>"
        "</div>"
        f"<div class='form-actions'><button class='btn'>{escape(操作('add_pattern'))}</button></div>"
        "</form></aside>"
    )
    # 表が主役 — 空のときだけ、この製品で本当のことを1行言う（"No data" は言わない）
    表 = (
        "<div class='wrap'><table><tr><th>Patient</th><th>Weekday</th><th>Cadence</th>"
        "<th>Clinician</th><th>Purpose</th><th>From</th><th>To</th><th></th></tr>"
        + 行 + "</table></div>"
        if rows else
        "<p class='empty'>No agreement is on record. Planned visits derive from"
        " agreements — record one and Troupe's pulse expands it into the calendar.</p>"
    )
    return (
        頭
        + バナー
        + "<div class='agreements-layout'>"
        "<div class='agreements-table'>"
        + 表 + "</div>"
        + form
        + "</div>"
        # この頁だけの並び — 表が主役で幅を取り、form-card は右の脇に1枚だけ。正本の style は触らない
        + "<style>"
        ".agreements-layout { display: grid; grid-template-columns: minmax(0, 1fr);"
        " gap: 24px; align-items: start; }"
        ".agreements-layout .form-card { margin-top: 0; }"
        "@media (min-width: 1160px) {"
        " .agreements-layout { grid-template-columns: minmax(0, 1fr) 340px; gap: 36px; } }"
        "</style>"
    )
