from __future__ import annotations
from app.dto.detail_view import DetailView
from html import escape
from ui.web.frame import _押せること
from ui.web.frame import _欄
from ui.web.frame import _状態
from ui.words import ACTOR_GLOSS
from ui.words import 出来事
from ui.words import 語
from ui.words import 起こす者

#: 2面の並びはこの頁だけのもの——枠の1枚（style.py）に足さず、頁が持って出る。
#: 中は**箱を重ねない**: 欄は紙の上に直に、問答と見立ては引用の段（左の髪線）、
#: 出来事は罫線の行。色の帯は置かない。
_様式 = """<style>
/* 詳細の頭 — やること・状態・識別子と期日 */
.detail-head { margin: 0 0 20px; padding: 0 0 12px; border-bottom: 1px solid var(--line); }
.detail-head__top { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.detail-head__top .page-title { margin: 0; }
.detail-head__meta { margin: 6px 0 0; font-size: 13px; color: var(--muted); }
/* 詳細の2面 — 左（欄・問答・見立て）/ 右（出来事の列）。1100px 未満で1段 */
.detail-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 28px 34px; align-items: start; }
.detail-main, .detail-side { min-width: 0; }
@media (min-width: 1100px) {
  .detail-grid { grid-template-columns: minmax(0, 58fr) minmax(320px, 42fr); }
}
/* 欄の段 — 箱ではなく、紙の上の dl。操作は髪線1本の下 */
.detail-record { margin: 0 0 24px; }
.detail-record dl { margin: 0; }
.detail-record__actions {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--line);
}
.detail-record__actions:first-child { margin-top: 0; padding-top: 0; border-top: 0; }
/* 引用の段 — 問答の対と見立て。左の余白と髪線だけ（色の帯は置かない） */
.detail-quote {
  border-left: 1px solid var(--line-strong);
  padding: 2px 0 2px 16px; margin: 0 0 16px;
}
.detail-quote__line { margin: 0; white-space: pre-wrap; }
.detail-quote__line + .detail-quote__line { margin-top: 8px; }
.detail-quote__line--pending { color: var(--muted); }
.detail-quote__tag {
  display: inline-block; font-size: 10.5px; font-weight: 650;
  letter-spacing: .07em; text-transform: uppercase; color: var(--muted);
  margin-right: 8px;
}
.detail-quote__why { margin: 6px 0 0; font-size: 13px; color: var(--muted); white-space: pre-wrap; }
/* 出来事の列 — 罫線の行。頭は髪線の下の小見出し */
.detail-side__title {
  font-size: 12px; font-weight: 650; letter-spacing: .07em;
  text-transform: uppercase; color: var(--muted);
  margin: 0 0 8px; padding: 0 0 6px; border-bottom: 1px solid var(--line);
}
.detail-events td { padding: 8px 8px; }
.detail-events th { padding: 6px 8px; }
.detail-events td:first-child, .detail-events th:first-child { padding-left: 0; }
.detail-events .who { font-size: 12.5px; }
/* 帳簿の最新行（列は古い→新しいなので最後の行）——着いたばかりの色が静かに引く */
.detail-events tr:last-child td { animation: freshrow 2.4s ease-out 1; }
@media (prefers-reduced-motion: reduce) {
  .detail-events tr:last-child td { animation: none; }
}
</style>"""

#: 起こす者の語 → 点の色の類。名で届いたときは種別が分からない——素の点のまま出す。
_WHO = {"人": "who--human", "AI": "who--agent", "時計": "who--clock"}


def _誰(by: str) -> str:
    """出来事の「誰が」。語なら種別の点、名なら素の点——**種別を発明しない**。"""
    cls = _WHO.get(by, "")
    名 = 起こす者(by) if by in ACTOR_GLOSS else by
    return (f"<span class='who{' ' + cls if cls else ''}'>"
            f"<span class='who-dot'></span>{escape(名)}</span>")


def _詳細(view: DetailView | None) -> str:
    if view is None:
        return ("<p class='empty'>No job with this id — "
                "the ledger has no such entry.</p>")
    頭 = (
        "<div class='detail-head'><div class='detail-head__top'>"
        f"<h1 class='page-title'>{escape(view.instruction)}</h1>{_状態(view.state_name)}</div>"
        f"<p class='detail-head__meta'><span class='id'>{escape(view.id)}</span>"
        f" · {escape(語('期日'))} <span class='cell-when'>{escape(view.due)}</span></p></div>"
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
        行動 = f"<div class='detail-record__actions'>{押せる}</div>" if 押せる else ""
        札 = f"<section class='detail-record'>{欄組}{行動}</section>"
    問答の段 = "".join(
        f"<div class='detail-quote'><p class='detail-quote__line'>"
        f"<span class='detail-quote__tag'>{escape(語('質問'))}</span>{escape(q)}</p>"
        + (
            f"<p class='detail-quote__line'>"
            f"<span class='detail-quote__tag'>{escape(語('回答'))}</span>{escape(a)}</p>"
            if a
            else f"<p class='detail-quote__line detail-quote__line--pending'>"
            f"<span class='detail-quote__tag'>{escape(語('回答'))}</span>(not yet)</p>"
        )
        + "</div>"
        for q, a in view.questions
    )
    見立ての段 = "".join(
        f"<div class='detail-quote'><p class='detail-quote__line'>"
        f"<span class='detail-quote__tag'>{escape(語('見立て'))}</span>{escape(本文)}</p>"
        f"<p class='detail-quote__why'>{escape(理由)}</p></div>"
        for 本文, 理由 in view.assessments
    )
    出来事の列 = "".join(
        f"<tr><td class='cell-when'>{escape(e.at)}</td><td>{_誰(e.by)}</td>"
        f"<td>{escape(出来事(e.what))}</td></tr>"
        for e in view.events
    )
    return (
        頭 + _様式
        + "<div class='detail-grid'><div class='detail-main'>"
        + 札 + 問答の段 + 見立ての段
        + "</div><aside class='detail-side'>"
        + "<p class='detail-side__title'>History</p>"
        + "<div class='wrap'><table class='detail-events'>"
        + "<tr><th>When</th><th>Who</th><th>What happened</th></tr>"
        + 出来事の列
        + "</table></div></aside></div>"
    )
