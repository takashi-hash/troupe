from __future__ import annotations
from app.dto.fee_row import FeeRow
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



#: 2面の並びはこの頁だけのもの——枠の1枚（style.py）に足さず、頁が持って出る。
_様式 = """<style>
/* 訪問の2面 — 左（患者札と下書き・貼り付く）/ 右（記録の欄）。1100px 未満で1段 */
.visit-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0 34px; align-items: start; }
.visit-aside, .visit-main { min-width: 0; }
@media (min-width: 1100px) {
  .visit-grid { grid-template-columns: minmax(300px, 43fr) minmax(0, 57fr); }
  .visit-aside { position: sticky; top: 22px; max-height: calc(100vh - 44px); overflow-y: auto; }
}
/* 行為と薬剤の札 — 1行1項目、右端に取り消し。追加は1行に収める */
.visit-svc ul { list-style: none; margin: 0 0 4px; padding: 0; }
.visit-svc__row { display: flex; align-items: center; justify-content: space-between;
                  gap: 8px; padding: 3px 0; }
.visit-svc__row form { margin: 0; }
.visit-svc__add { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.visit-svc__add select { flex: 1 1 auto; min-width: 0; }
.visit-svc__qty { width: 4.5em; }
</style>"""


def _行為札(view: VisitView, fees: tuple[FeeRow, ...]) -> str:
    """Services & medications——予定中は足し引きでき、署名で凍る。"""
    予定中 = view.status == "scheduled"
    行々 = []
    for code, name, qty in view.services:
        取り消し = ""
        if 予定中:
            取り消し = (
                "<form method='post' action='/visit/act'>"
                "<input type='hidden' name='what' value='remove_service'>"
                f"<input type='hidden' name='id' value='{escape(view.id)}'>"
                f"<input type='hidden' name='code' value='{escape(code)}'>"
                "<button class='btn btn--small btn--destructive'>Remove</button></form>"
            )
        行々.append(
            f"<li class='visit-svc__row'><span>{escape(code)} · {escape(name)}"
            f" × {qty}</span>{取り消し}</li>"
        )
    一覧 = f"<ul>{''.join(行々)}</ul>" if 行々 else ""
    if 予定中:
        選択肢 = []
        for f in fees:
            if f.kind in ("visit", "oncall", "monthly"):
                continue
            値段 = " / ".join(
                部 for 部 in (
                    f"{f.points} pts" if f.points is not None else None,
                    f"¥{f.price_yen}" if f.price_yen is not None else None,
                ) if 部
            )
            選択肢.append(
                f"<option value='{escape(f.code)}'>"
                f"{escape(f'{f.code} · {f.name} ({値段})')}</option>"
            )
        中身 = 一覧 or "<p class='sub'>Nothing recorded yet.</p>"
        中身 += (
            "<form class='visit-svc__add' method='post' action='/visit/act'>"
            "<input type='hidden' name='what' value='add_service'>"
            f"<input type='hidden' name='id' value='{escape(view.id)}'>"
            f"<select name='code'>{''.join(選択肢)}</select>"
            "<input class='visit-svc__qty' type='number' name='qty' value='1' min='1'>"
            "<button class='btn btn--small'>Add</button></form>"
            "<p class='sub'>The visit fee itself derives automatically from the"
            " signed visit — enter only what was done.</p>"
        )
    else:
        中身 = 一覧 or "<p class='sub'>Nothing recorded.</p>"
        中身 += "<p class='sub'>Frozen by signing — this list can no longer change.</p>"
    return (
        "<div class='card visit-svc'><div class='snapshot__head'>"
        "<span class='snapshot__title'>Services &amp; medications</span></div>"
        + 中身
        + "<p class='sub'>Every code, point value and payer here is invented"
        " — the Nagisa Schedule is fictional.</p></div>"
    )


def _訪問(view: VisitView | None, 断り: str | None = None,
        fees: tuple[FeeRow, ...] = ()) -> str:
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
    )
    患者札 = (
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
        return (
            頭 + _様式
            + f"<div class='visit-grid'><div class='visit-aside'>{患者札}{_行為札(view, fees)}</div>"
            + f"<div class='visit-main'><p class='sub'>This visit is {escape(view.status)}"
            " — read-only.</p>" + 済み + "</div></div>"
        )
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
    return (
        頭 + _様式
        + f"<div class='visit-grid'><div class='visit-aside'>{患者札}{下書きパネル}{_行為札(view, fees)}</div>"
        + f"<div class='visit-main'>{編集}</div></div>"
        + 休み
    )


