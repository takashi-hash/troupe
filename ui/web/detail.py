from __future__ import annotations
from app.dto.detail_view import DetailView
from html import escape
from ui.web.frame import _押せること
from ui.web.frame import _欄
from ui.web.frame import _状態
from ui.words import 出来事
from ui.words import 語
from ui.words import 起こす者

#: 2面の並びはこの頁だけのもの——枠の1枚（style.py）に足さず、頁が持って出る。
_様式 = """<style>
/* 詳細の頭 — やること・状態・識別子と期日 */
.detail-head { margin: 0 0 18px; }
.detail-head__top { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.detail-head__top .page-title { margin: 0; }
.detail-head__meta { margin: 5px 0 0; font-size: 13px; color: var(--muted); }
/* 詳細の2面 — 左（欄・問答・見立て）/ 右（出来事の列）。1100px 未満で1段 */
.detail-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 28px 34px; align-items: start; }
.detail-main, .detail-side { min-width: 0; }
@media (min-width: 1100px) {
  .detail-grid { grid-template-columns: minmax(0, 58fr) minmax(320px, 42fr); }
}
.detail-side__title {
  font-size: 12px; font-weight: 650; letter-spacing: .07em;
  text-transform: uppercase; color: var(--muted); margin: 0 0 8px;
}
/* 静かな札 — 問答の対と見立て。色は置かない */
.qa-card {
  border: 1px solid var(--line); border-radius: 10px;
  background: var(--faint); padding: 12px 16px; margin: 0 0 12px;
}
.qa-card__line { margin: 0; white-space: pre-wrap; }
.qa-card__line + .qa-card__line { margin-top: 8px; }
.qa-card__line--pending { color: var(--muted); }
.qa-card__tag {
  display: inline-block; font-size: 10.5px; font-weight: 650;
  letter-spacing: .07em; text-transform: uppercase; color: var(--muted);
  margin-right: 8px;
}
.qa-card__why { margin: 6px 0 0; font-size: 13px; color: var(--muted); white-space: pre-wrap; }
</style>"""


def _詳細(view: DetailView | None) -> str:
    if view is None:
        return "<p class='empty'>No such job.</p>"
    頭 = (
        "<div class='detail-head'><div class='detail-head__top'>"
        f"<h1 class='page-title'>{escape(view.instruction)}</h1>{_状態(view.state_name)}</div>"
        f"<p class='detail-head__meta'><span class='id'>{escape(view.id)}</span>"
        f" · {escape(語('期日'))} {escape(view.due)}</p></div>"
    )
    欄組 = _欄(
        [
            (語("担当"), view.assignee_name),
            (語("成果"), view.result_body),
            (語("根拠"), view.evidence_quote),
            (語("確かめ期日"), view.recheck_at),
        ]
    )
    押せる = _押せること(view.actions, view.id, f"/detail?id={view.id}")
    札 = ""
    if 欄組 or 押せる:
        行動 = f"<div class='{'card-actions' if 欄組 else 'actions'}'>{押せる}</div>" if 押せる else ""
        札 = f"<div class='row'>{欄組}{行動}</div>"
    問答の札 = "".join(
        f"<div class='qa-card'><p class='qa-card__line'>"
        f"<span class='qa-card__tag'>{escape(語('質問'))}</span>{escape(q)}</p>"
        + (
            f"<p class='qa-card__line'>"
            f"<span class='qa-card__tag'>{escape(語('回答'))}</span>{escape(a)}</p>"
            if a
            else f"<p class='qa-card__line qa-card__line--pending'>"
            f"<span class='qa-card__tag'>{escape(語('回答'))}</span>(not yet)</p>"
        )
        + "</div>"
        for q, a in view.questions
    )
    見立ての札 = "".join(
        f"<div class='qa-card'><p class='qa-card__line'>"
        f"<span class='qa-card__tag'>{escape(語('見立て'))}</span>{escape(本文)}</p>"
        f"<p class='qa-card__why'>{escape(理由)}</p></div>"
        for 本文, 理由 in view.assessments
    )
    出来事の列 = "".join(
        f"<tr><td class='cell-when'>{escape(e.at)}</td><td>{escape(起こす者(e.by))}</td>"
        f"<td>{escape(出来事(e.what))}</td></tr>"
        for e in view.events
    )
    return (
        頭 + _様式
        + "<div class='detail-grid'><div class='detail-main'>"
        + 札 + 問答の札 + 見立ての札
        + "</div><aside class='detail-side'>"
        + "<p class='detail-side__title'>History</p>"
        + "<div class='wrap'><table><tr><th>When</th><th>Who</th><th>What happened</th></tr>"
        + 出来事の列
        + "</table></div></aside></div>"
    )
