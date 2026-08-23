from __future__ import annotations
from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientView
from html import escape
from ui.web.frame import _md
from ui.web.frame import _欄
from urllib.parse import quote

def _患者たち(rows: tuple[PatientRow, ...], today: str = "") -> str:
    """患者の一覧 — 診療録の写し。**よその語のまま並べる**（翻訳しない）。"""
    # 期限切れの数は表の cell-danger と同じ条件で数える（正本は _期限）
    期限切れ = sum(
        1 for r in rows if r.order_expires and today and r.order_expires < today
    )
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Patients</h1>"
        f"<span class='count-pill'><strong>{len(rows)}</strong> patients</span>"
        + (
            f"<span class='page-head__aside'>{期限切れ} orders expired</span>"
            if 期限切れ else ""
        )
        + "</div>"
    )
    if not rows:
        return 頭 + (
            "<p class='empty'>The agency EMR is not wired (ICHIZA_EMR_DSN), "
            "or holds no patients.</p>"
        )
    def _期限(r: PatientRow) -> str:
        if not r.order_expires:
            return "<td>—</td>"
        if today and r.order_expires < today:
            return (f"<td class='cell-danger'><span class='chip chip--expired'>"
                    f"Expired {escape(r.order_expires)}</span></td>")
        return f"<td>{escape(r.order_expires)}</td>"

    行 = "".join(
        f"<tr><td><a class='patient-chip' href='/patient?code={quote(r.code)}'>{escape(r.code)}</a></td>"
        f"<td>{escape(r.age)}</td><td>{escape(r.diagnosis)}</td>"
        f"<td>{escape(r.living)}</td><td>{escape(r.next_visit or '—')}</td>"
        + _期限(r) + "</tr>"
        for r in rows
    )
    return (
        頭
        + "<p class='sub'>Read-only mirror of the agency EMR — synthetic data, no real patient exists. "
        "Troupe never writes here.</p>"
        # 絞り込みは飾り — JS が無ければ欄ごと出さず、表は常に全部読める
        "<div class='table-filter' hidden>"
        "<input type='text' id='patient-filter' aria-label='Filter patients'"
        " placeholder='Filter — code, diagnosis, living…' autocomplete='off'></div>"
        "<div class='wrap'><table id='patients-table'><tr><th>Code</th><th>Age</th><th>Diagnosis</th>"
        "<th>Living</th><th>Next visit</th><th>Order expires</th></tr>" + 行 + "</table></div>"
        "<script>(function () {"
        "var box = document.getElementById('patient-filter');"
        "box.closest('.table-filter').hidden = false;"
        "box.addEventListener('input', function () {"
        "  var q = box.value.trim().toLowerCase();"
        "  document.querySelectorAll('#patients-table tr').forEach(function (tr) {"
        "    if (tr.querySelector('th')) return;"
        "    tr.hidden = q !== '' && tr.textContent.toLowerCase().indexOf(q) < 0;"
        "  });"
        "});"
        "})();</script>"
        "<style>"
        ".table-filter { margin: 0 0 14px; }"
        ".table-filter input { width: 300px; max-width: 100%; }"
        "</style>"
    )


def _患者(view: PatientView | None) -> str:
    if view is None:
        return "<p class='empty'>No such patient.</p>"
    下書き = "".join(
        f"<article class='card note-card note-card--draft{' draft-panel--used' if d.used else ''}'>"
        f"<div class='card__head'>"
        f"<span class='seal {'seal--used' if d.used else 'seal--draft'}'>{'USED' if d.used else 'DRAFT'}</span>"
        f"<span class='note-card__meta'>delivered {escape(d.delivered_at[:16])}"
        f" · <a class='link-action' href='/detail?id={quote(d.job_id)}'>AI history →</a></span></div>"
        f"<div class='md'>{_md(d.body)}</div>"
        "<p class='note-card__foot sub'>A proposal from Troupe. A doctor rewrites and signs —"
        " this never becomes the record by itself.</p></article>"
        for d in view.drafts
    )
    記録 = "".join(
        f"<article class='card note-card note-card--signed'><div class='card__head'>"
        f"<span class='seal seal--signed'>SIGNED</span>"
        f"<span class='card__title'>Note {escape(n.at)}</span>"
        f"<span class='note-card__meta push'>{escape(n.clinician)} · signed {escape(n.signed_at[:16])}</span></div>"
        f"<dl class='soap'><dt>S</dt><dd>{escape(n.s)}</dd><dt>O</dt><dd>{escape(n.o)}</dd>"
        f"<dt>A</dt><dd>{escape(n.a)}</dd><dt>P</dt><dd>{escape(n.p)}</dd></dl></article>"
        for n in view.notes
    )
    return (
        f"<div class='row'><div class='head'>"
        f"<span class='title'>{escape(view.code)}</span>"
        f"<span class='id'>{escape(view.diagnosis)}</span></div>"
        + _欄(
            [
                ("Age", view.age),
                ("Living", view.living),
                ("Next visit", view.next_visit),
                ("Physician order", view.order),
                ("Medications", "\n".join(view.meds) or None),
                ("Condition events", "\n".join(view.events) or None),
            ]
        )
        + f"<p class='sub'><a href='/search?keyword={quote(view.code)}'>"
        f"Jobs for this patient →</a></p></div>"
        # 下書きと正記録は別の柱 — 混ぜて並べず、見出しつきの2欄で分ける
        + "<div class='chart-cols'>"
        "<section class='chart-col'><h3 class='chart-col__head'>Drafts — awaiting a clinician</h3>"
        + (下書き or "<p class='sub'>No drafts waiting.</p>")
        + "</section>"
        "<section class='chart-col'><h3 class='chart-col__head'>Signed record</h3>"
        + (記録 or "<p class='sub'>No signed notes yet.</p>")
        + "</section></div>"
        "<style>"
        ".chart-cols { display: grid; grid-template-columns: minmax(0, 1fr);"
        " gap: 28px; align-items: start; margin-top: 8px; }"
        "@media (min-width: 1100px) {"
        " .chart-cols { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 36px; } }"
        ".chart-col__head { margin: 0 0 12px; font-size: 11.5px; font-weight: 600;"
        " letter-spacing: .07em; text-transform: uppercase; color: var(--muted); }"
        "</style>"
    )
