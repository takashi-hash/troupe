from __future__ import annotations
from app.dto.visit_view import VisitView
from html import escape
from ui.web.frame import _md
from ui.web.frame import _欄
from urllib.parse import quote

import re as _re


def _soap分解(body: str) -> dict[str, str] | None:
    """下書きから S/O/A/P を最善努力で切り出す。切れなければ None——発明しない。"""
    見出し = _re.compile(
        r"^\s*(?:#+\s*)?\**\(?(S|O|A|P)\)?\**\s*(?:\(Subjective\)|\(Objective\)|\(Assessment\)|\(Plan\))?\**\s*[:：]?\s*$",
        _re.M,
    )
    切れ目 = [(m.group(1), m.end()) for m in 見出し.finditer(body)]
    if [k for k, _ in 切れ目] != ["S", "O", "A", "P"]:
        return None
    out: dict[str, str] = {}
    for i, (k, start) in enumerate(切れ目):
        end = 切れ目[i + 1][1] - len(body[切れ目[i + 1][1]:]) if False else (
            見出し.finditer(body) and None)
    # 位置で切る
    位置 = [start for _, start in 切れ目] + [len(body)]
    始まりの行 = [m.start() for m in 見出し.finditer(body)] + [len(body)]
    for i, (k, _) in enumerate(切れ目):
        out[k.lower()] = body[位置[i]:始まりの行[i + 1]].strip().strip("-* ").strip()
    return out if all(out.values()) else None



def _訪問(view: VisitView | None, 断り: str | None = None) -> str:
    if view is None:
        return "<p class='empty'>No such visit.</p>"
    pt = view.patient
    期限 = ""
    if pt.order_expires:
        期限 = (f"<dt>Physician order</dt><dd>expires "
                f"<span class='chip chip--expiring'>{escape(pt.order_expires)}</span></dd>")
    頭 = (
        f"<p class='crumbs'><a href='/day?day={quote(view.visit_date)}'>My Day</a>"
        f" → {escape(pt.code)} · Visit</p>"
        f"<div class='visit-head'><h1 class='page-title'>{escape(pt.code)} · Visit</h1>"
        f"<span class='chip'>{escape(view.status.capitalize())}</span>"
        f"<span class='visit-head__meta'>{escape(view.visit_date)} · {escape(view.clinician)}</span></div>"
        f"<div class='card snapshot'><div class='snapshot__head'>"
        f"<span class='snapshot__title'>Patient snapshot</span>"
        f"<a class='link-action push' href='/patient?code={quote(pt.code)}'>Full chart →</a></div>"
        f"<dl><dt>Diagnosis</dt><dd>{escape(pt.diagnosis)}</dd>"
        f"<dt>Age · Living</dt><dd>{escape(pt.age)} · {escape(pt.living)}</dd>"
        f"<dt>Purpose</dt><dd>{escape(view.purpose)}</dd>{期限}</dl></div>"
    )
    if view.status != "scheduled":
        済み = "".join(
            f"<div class='row'><div class='head'><span class='state state-final'>SIGNED</span>"
            f"<span class='title'>Note {escape(n.at)}</span>"
            f"<span class='id'>{escape(n.clinician)} · signed {escape(n.signed_at[:16])}</span></div>"
            + _欄([("S", n.s), ("O", n.o), ("A", n.a), ("P", n.p)]) + "</div>"
            for n in view.notes[:1]
        )
        return 頭 + f"<p class='sub'>This visit is {escape(view.status)} — read-only.</p>" + 済み
    draft = view.drafts[0] if view.drafts else None
    分解 = _soap分解(draft.body) if draft else None
    下書きパネル = ""
    if draft:
        下書きパネル = (
            "<details class='fold draft-panel' open><summary>"
            f"<span class='seal seal--draft'>DRAFT</span>"
            "<span class='draft-panel__kicker'> A proposal, not the record</span>"
            f"<span class='sub'> · delivered {escape(draft.delivered_at)}</span></summary>"
            f"<div class='draft-panel__body md'>{_md(draft.body)}</div>"
            "<p class='sub'>"
            + ("Prefilled into the editor below"
               if 分解 else "Could not be split into S/O/A/P — copy what you need")
            + ". The doctor rewrites and signs; the draft is never the record.</p></details>"
        )
    説明 = {"s": "What the patient reports.", "o": "What you observe and measure.",
            "a": "Your clinical judgment.", "p": "What happens next — checks first."}

    def 欄(名: str, key: str) -> str:
        中身 = (分解 or {}).get(key, "")
        return (f"<div class='note-field'><label for='f-{key}'>{名}</label>"
                f"<p class='hint'>{説明[key]}</p>"
                f"<textarea id='f-{key}' name='{key}' rows='6' required>{escape(中身)}</textarea></div>")
    署名者 = "".join(
        f"<option{' selected' if c == view.clinician else ''}>{escape(c)}</option>"
        for c in view.clinicians
    )
    編集 = (
        f"<form class='note-editor' method='post' action='/visit/act'>"
        f"<input type='hidden' name='what' value='sign_note'>"
        f"<input type='hidden' name='id' value='{escape(view.id)}'>"
        + (f"<input type='hidden' name='draft_id' value='{escape(draft.id)}'>" if draft else "")
        + 欄("S — Subjective", "s") + 欄("O — Objective", "o")
        + 欄("A — Assessment", "a") + 欄("P — Plan", "p")
        + "<div class='sign-bar'><span class='sign-bar__meta'>"
        f"{escape(pt.code)} · {escape(view.visit_date)} — a signed note is permanent"
        " and cannot be edited</span>"
        "<span class='sign-bar__actions'><label>Signing as <select name='signer'>"
        + 署名者 + "</select></label>"
        "<button class='btn btn--primary' onclick=\"return confirm('Sign this note and complete the visit? A signed record cannot be changed.')\">"
        "Sign and complete visit</button></span></div></form>"
    )
    休み = (
        "<div class='cancel-zone'><details class='fold'>"
        "<summary>This visit didn't happen?</summary>"
        f"<form class='act' method='post' action='/visit/act'>"
        f"<input type='hidden' name='what' value='cancel_visit'>"
        f"<input type='hidden' name='id' value='{escape(view.id)}'>"
        "<label>Reason <input type='text' name='reason' required></label>"
        "<button class='btn btn--destructive' onclick=\"return confirm('Cancel this one visit? The agreement stays.')\">Cancel this visit only</button></form>"
        "<p class='sub'>The agreement stays — only this one visit is cancelled.</p>"
        "</details></div>"
    )
    return 頭 + 下書きパネル + 編集 + 休み


