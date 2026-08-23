from __future__ import annotations
from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientView
from html import escape
from ui.web.frame import _md
from ui.web.frame import _欄
from urllib.parse import quote

def _患者たち(rows: tuple[PatientRow, ...], today: str = "") -> str:
    """患者の一覧 — 診療録の写し。**よその語のまま並べる**（翻訳しない）。"""
    if not rows:
        return (
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
        "<p class='sub'>Read-only mirror of the agency EMR — synthetic data, no real patient exists. "
        "Troupe never writes here.</p>"
        "<div class='wrap'><table><tr><th>Code</th><th>Age</th><th>Diagnosis</th>"
        "<th>Living</th><th>Next visit</th><th>Order expires</th></tr>" + 行 + "</table></div>"
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
        + 下書き
        + 記録
    )


