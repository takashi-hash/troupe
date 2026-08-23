from __future__ import annotations
from app.dto.patient_row import PatientRow
from app.dto.patient_view import PatientView
from app.dto.pattern_row import PatternRow
from html import escape
from ui.web.agreements import _取り決め数
from ui.web.agreements import _取り決め表
from ui.web.agreements import _取り決めフォーム
from ui.web.agreements import _患者の取り決めフォーム
from ui.web.agreements import _追加バナー
from ui.web.frame import _md
from ui.web.frame import _欄
from urllib.parse import quote

#: 右レールの列組 — 表が主役で幅を取り、人の操作は右の脇。狭い幅では下に積む（消さない）
_列組 = (
    ".page-cols { display: grid; grid-template-columns: minmax(0, 1fr) 340px;"
    " gap: 28px; align-items: start; }"
    ".page-rail { position: sticky; top: 20px; }"
    "@media (max-width: 1100px) { .page-cols { display: block; }"
    " .page-rail { position: static; margin-top: 24px; } }"
)


def _取り決め節(patterns: tuple[PatternRow, ...], added: str | None) -> str:
    """一覧頁の下に足す罫の節 — 表が主役、右レールに結びフォーム。"""
    有効, 終了 = _取り決め数(patterns)
    return (
        "<section class='pl-agreements'>"
        "<div class='pl-agr-head'><h2 class='pl-agr-title'>Agreements in force</h2>"
        f"<span class='count-pill'><strong>{有効}</strong> in force</span>"
        + (f"<span class='pl-agr-aside'>{終了} ended</span>" if 終了 else "")
        + "</div>"
        + _追加バナー(added)
        + "<p class='sub'>An agreement is a fact about the patient — it lives here,"
        " and the pulse expands it into the calendar.</p>"
        "<div class='page-cols'><div class='page-main'>"
        + _取り決め表(patterns)
        + "</div><aside class='page-rail'>"
        + _取り決めフォーム("/patients")
        + "</aside></div></section>"
        "<style>"
        ".pl-agreements { border-top: 1px solid var(--line-strong);"
        " margin-top: 32px; padding-top: 20px; }"
        ".pl-agr-head { display: flex; align-items: baseline; gap: 12px;"
        " flex-wrap: wrap; margin: 0 0 4px; }"
        ".pl-agr-title { font-family: var(--serif); font-size: 17px;"
        " font-weight: 600; margin: 0; }"
        ".pl-agr-aside { margin-left: auto; font-size: 13.5px; color: var(--muted); }"
        ".pl-agreements .form-card { margin-top: 0; }"
        + _列組 +
        "</style>"
    )


def _患者たち(
    rows: tuple[PatientRow, ...],
    today: str = "",
    patterns: tuple[PatternRow, ...] = (),
    added: str | None = None,
) -> str:
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
        # 取り決めは一座の帳簿のもの — EMR の鏡が空でも節は出す
        return 頭 + (
            "<p class='empty'>The agency EMR is not wired (ICHIZA_EMR_DSN), "
            "or holds no patients.</p>"
        ) + _取り決め節(patterns, added)
    def _期限(r: PatientRow) -> str:
        if not r.order_expires:
            return "<td class='cell-when'>—</td>"
        if today and r.order_expires < today:
            return (f"<td class='cell-danger'><span class='chip chip--expired'>"
                    f"Expired {escape(r.order_expires)}</span></td>")
        return f"<td class='cell-when'>{escape(r.order_expires)}</td>"

    行 = "".join(
        f"<tr><td><a class='patient-chip' href='/patient?code={quote(r.code)}'>{escape(r.code)}</a></td>"
        f"<td class='patients-num'>{escape(r.age)}</td><td>{escape(r.diagnosis)}</td>"
        f"<td>{escape(r.living)}</td><td class='cell-when'>{escape(r.next_visit or '—')}</td>"
        + _期限(r) + "</tr>"
        for r in rows
    )
    return (
        頭
        + "<p class='sub'>Read-only mirror of the agency EMR — synthetic data, no real patient exists. "
        "Troupe never writes here.</p>"
        # 絞り込みは飾り — JS が無ければ欄ごと出さず、表は常に全部読める
        "<div class='patients-filter' hidden>"
        "<input type='text' id='patient-filter' aria-label='Filter patients'"
        " placeholder='Filter — code, diagnosis, living…' autocomplete='off'></div>"
        "<div class='wrap'><table id='patients-table'><tr><th>Code</th>"
        "<th class='patients-num'>Age</th><th>Diagnosis</th>"
        "<th>Living</th><th>Next visit</th><th>Order expires</th></tr>" + 行 + "</table></div>"
        + _取り決め節(patterns, added)
        + "<script>(function () {"
        "var box = document.getElementById('patient-filter');"
        "box.closest('.patients-filter').hidden = false;"
        "box.addEventListener('input', function () {"
        "  var q = box.value.trim().toLowerCase();"
        "  document.querySelectorAll('#patients-table tr').forEach(function (tr) {"
        "    if (tr.querySelector('th')) return;"
        "    tr.hidden = q !== '' && tr.textContent.toLowerCase().indexOf(q) < 0;"
        "  });"
        "});"
        "})();</script>"
        "<style>"
        ".patients-filter { margin: 0 0 14px; }"
        ".patients-filter input { width: 300px; max-width: 100%; }"
        # 年齢は数 — 右寄せ・等幅数字で桁が縦に揃う（th は class が既定の左寄せに勝つ）
        ".patients-num { text-align: right; }"
        "</style>"
    )


def _患者(
    view: PatientView | None,
    patterns: tuple[PatternRow, ...] = (),
    added: str | None = None,
) -> str:
    if view is None:
        return "<p class='empty'>No patient with that code exists in the EMR mirror.</p>"
    # 柱の中の note-card が唯一の枠（紙の上のカードは1段まで）——頭は枠でなく罫線で区切る
    下書き = "".join(
        f"<article class='note-card note-card--draft{' draft-panel--used' if d.used else ''}'>"
        f"<div class='card__head'>"
        f"<span class='seal {'seal--used' if d.used else 'seal--draft'}'>{'USED' if d.used else 'DRAFT'}</span>"
        f"<span class='note-card__meta'>delivered <span class='num'>{escape(d.delivered_at[:16])}</span>"
        f" · <a class='link-action' href='/detail?id={quote(d.job_id)}'>AI history →</a></span></div>"
        f"<div class='md'>{_md(d.body)}</div>"
        "<p class='note-card__foot sub'>A proposal from Troupe. A doctor rewrites and signs —"
        " this never becomes the record by itself.</p></article>"
        for d in view.drafts
    )
    記録 = "".join(
        f"<article class='note-card note-card--signed'><div class='card__head'>"
        f"<span class='seal seal--signed'>SIGNED</span>"
        f"<span class='card__title'>Note <span class='num'>{escape(n.at)}</span></span>"
        f"<span class='note-card__meta push'>{escape(n.clinician)} · signed "
        f"<span class='num'>{escape(n.signed_at[:16])}</span></span></div>"
        f"<dl class='soap'><dt>S</dt><dd>{escape(n.s)}</dd><dt>O</dt><dd>{escape(n.o)}</dd>"
        f"<dt>A</dt><dd>{escape(n.a)}</dd><dt>P</dt><dd>{escape(n.p)}</dd></dl></article>"
        for n in view.notes
    )
    def _柱頭(名: str, 数: int) -> str:
        return (f"<h3 class='patient-col__head'>{名}"
                + (f"<span class='patient-col__n num'>{数}</span>" if 数 else "")
                + "</h3>")
    return (
        # 患者の素性は紙に直に書く — 枠で囲わず、罫線1本で診療録の柱と区切る
        "<section class='patient-idblock'>"
        "<div class='patient-hd'>"
        f"<h2 class='patient-hd__code'>{escape(view.code)}</h2>"
        f"<span class='patient-hd__dx'>{escape(view.diagnosis)}</span>"
        f"<a class='link-action patient-hd__jobs' href='/search?keyword={quote(view.code)}'>"
        "Jobs for this patient →</a></div>"
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
        + "</section>"
        # 取り決めは患者についての事実 — 素性と診療録の柱のあいだに、罫の節で置く
        + "<section class='pd-agreements'>"
        + _柱頭("Agreements", sum(1 for r in patterns if r.active_to is None))
        + _追加バナー(added)
        + "<div class='page-cols'><div class='page-main'>"
        + _取り決め表(
            patterns,
            back=f"/patient?code={quote(view.code)}",
            患者列=False,
            空文="No agreement yet — record one and Monday's pulse plans the visits.",
        )
        + "</div><aside class='page-rail'>"
        + _患者の取り決めフォーム(view.code, f"/patient?code={quote(view.code)}")
        + "</aside></div></section>"
        # 下書きと正記録は別の柱 — 混ぜて並べず、見出しつきの2欄で分ける
        + "<div class='patient-cols'>"
        "<section class='patient-col'>" + _柱頭("Drafts — awaiting a clinician", len(view.drafts))
        + (下書き or "<p class='sub'>No draft is waiting. When Troupe prepares a visit note"
                     " for this patient, it appears here for a clinician to rewrite and sign.</p>")
        + "</section>"
        "<section class='patient-col'>" + _柱頭("Signed record", len(view.notes))
        + (記録 or "<p class='sub'>No signed notes yet — a note enters this chart"
                   " only when a clinician signs it.</p>")
        + "</section></div>"
        "<style>"
        ".patient-hd { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }"
        # 見出しは記録の書体（serif）、ただし ID の数字は等幅数字で
        ".patient-hd__code { font-family: var(--serif); font-size: 21px; font-weight: 600;"
        " font-variant-numeric: tabular-nums; margin: 0; }"
        ".patient-hd__dx { font-size: 13.5px; color: var(--muted); }"
        ".patient-hd__jobs { margin-left: auto; font-size: 13.5px; }"
        ".patient-idblock { border-bottom: 1px solid var(--line-strong);"
        " padding-bottom: 20px; margin-bottom: 24px; }"
        ".patient-cols { display: grid; grid-template-columns: minmax(0, 1fr);"
        " gap: 28px; align-items: start; }"
        "@media (min-width: 1100px) {"
        " .patient-cols { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 36px; } }"
        ".patient-col__head { display: flex; align-items: baseline; gap: 8px;"
        " margin: 0 0 14px; font-family: var(--serif); font-size: 16px; font-weight: 600;"
        " border-bottom: 1px solid var(--line); padding-bottom: 7px; }"
        ".patient-col__n { margin-left: auto; font-size: 12.5px; font-weight: 500;"
        " color: var(--muted); }"
        ".pd-agreements { border-bottom: 1px solid var(--line-strong);"
        " padding-bottom: 20px; margin-bottom: 24px; }"
        ".pd-agreements .form-card { margin-top: 0; }"
        + _列組 +
        "</style>"
    )
