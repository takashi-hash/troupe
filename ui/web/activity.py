"""履歴（Activity）— 過去に何を頼み、何が済んだ？（人に見えるもの §1）

誰が＝**種別と名**——種別のチップが人・AI・時計の見分けになる（§2 履歴の行）。
列は新しい順に区切って引ける——頁の送りはここが出す。
"""

from __future__ import annotations

from html import escape

from app.dto.history_row import HistoryRow
from ui.words import ACTOR_GLOSS, 出来事, 読める

#: 種別 → （チップの類・画面の名）。**種別は識別子で届く**——ここは見た目だけ。
_WHO = {
    "human": ("who--human", "Human"),
    "agent": ("who--agent", "AI"),
    "clock": ("who--clock", "Clock"),
}


def _誰(by: str, kind: str) -> str:
    cls, label = _WHO.get(kind, ("", kind))
    # 名が無いとき by には起こす者の語(和語)が入る——橋で識別子に写す(訳を発明しない)
    名 = 読める(ACTOR_GLOSS[by]) if by in ACTOR_GLOSS else by
    小 = "" if 名.lower() == label.lower() else f"<small>{escape(label)}</small>"
    return (
        f"<span class='who {cls}'><span class='who-dot'></span>"
        f"{escape(名)}{小}</span>"
    )


def _頁送り(page: int, per: int, count: int) -> str:
    """新しい方・古い方。行が頁いっぱいなら、まだ先があるとみなす。"""
    parts: list[str] = []
    if page > 0:
        parts.append(f"<a class='pager-link' href='/activity?page={page - 1}'>← Newer</a>")
    if count == per:
        parts.append(f"<a class='pager-link' href='/activity?page={page + 1}'>Older →</a>")
    if not parts:
        return ""
    return (
        "<nav class='pager'>" + " ".join(parts)
        + f"<span class='pager-page'>page {page + 1}</span></nav>"
    )


def _履歴(
    rows: tuple[HistoryRow, ...], page: int = 0, per: int = 100, total: int = 0
) -> str:
    始 = page * per + 1 if rows else 0
    終 = page * per + len(rows)
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Activity</h1>"
        f"<span class='count-pill'><strong>{total}</strong> events</span>"
        + (f"<span class='page-head__aside'>showing {始}–{終}</span>" if rows else "")
        + "</div>"
    )
    副題 = ("<p class='page-sub'>Every event ever appended to the ledger — who did "
            "what, newest first. Nothing here is ever overwritten or deleted.</p>")
    行 = "".join(
        f"<tr><td class='cell-when'>{escape(r.at)}</td><td>{_誰(r.by, r.by_kind)}</td>"
        f"<td>{escape(出来事(r.what))}</td>"
        f"<td><a class='id' href='/detail?id={escape(r.job_id)}'>{escape(r.head)}</a></td></tr>"
        for r in rows
    )
    empty = "" if rows else "<p class='empty'>No events on this page.</p>"
    return (
        頭
        + 副題
        + "<div class='wrap'><table><tr><th>When</th><th>Who</th><th>What happened</th>"
        "<th>Job</th></tr>" + 行 + "</table></div>"
        + empty
        + _頁送り(page, per, len(rows))
    )
