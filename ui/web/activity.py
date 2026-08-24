"""履歴（Activity）— 過去に何を頼み、何が済んだ？（人に見えるもの §1）

誰が＝**種別と名**——種別のチップが人・AI・時計の見分けになる（§2 履歴の行）。
列は新しい順に区切って引ける——頁の送りはここが出す。

帳簿の表がこの頁の顔——等幅の時刻・誰がのチップ・等幅数字。
最新行の引いていく色（.ledger-events の1行目）は style.py §6 の脈。
"""

from __future__ import annotations

from html import escape

from app.dto.history_row import HistoryRow
from ui.web.frame import _面切替
from ui.words import ACTOR_GLOSS, 出来事, 読める

#: 種別 → （チップの類・画面の名）。**種別は識別子で届く**——ここは見た目だけ。
_WHO = {
    "human": ("who--human", "Human"),
    "agent": ("who--agent", "AI"),
    "clock": ("who--clock", "Clock"),
}

#: 表の小さな整えはこの頁だけのもの——枠の1枚（style.py）に足さず、頁が持って出る。
_様式 = """<style>
/* 帳簿の表 — 4pxの目で詰める。見出し(Job)は等幅のまま1行で切り、行の高さを揃える */
.activity-ledger td { padding: 8px 12px; }
.activity-ledger .activity-job a {
  display: inline-block; max-width: 36ch; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; vertical-align: bottom;
}
</style>"""


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
        + f"<span class='pager-page num'>page {page + 1}</span></nav>"
    )


def _履歴(
    rows: tuple[HistoryRow, ...], page: int = 0, per: int = 100, total: int = 0
) -> str:
    始 = page * per + 1 if rows else 0
    終 = page * per + len(rows)
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Ledger</h1>"
        f"<span class='count-pill'><strong>{total}</strong> events</span>"
        + (f"<span class='page-head__aside num'>showing {始}–{終}</span>" if rows else "")
        + "</div>"
        + _面切替([("Events", "/activity", True), ("Jobs", "/search", False)])
    )
    副題 = ("<p class='page-sub'>Every event ever appended to the ledger — who did "
            "what, newest first. Nothing here is ever overwritten or deleted.</p>")
    行 = "".join(
        f"<tr><td class='cell-when'>{escape(r.at)}</td><td>{_誰(r.by, r.by_kind)}</td>"
        f"<td>{escape(出来事(r.what))}</td>"
        f"<td class='activity-job'>"
        f"<a class='id' href='/detail?id={escape(r.job_id)}'>{escape(r.head)}</a></td></tr>"
        for r in rows
    )
    # 空の言葉は本当のことを——1頁目は帳簿の性質、先の頁は端に着いたこと
    if rows:
        empty = ""
    elif page == 0:
        empty = ("<p class='empty'>The ledger starts writing itself the moment "
                 "a rule is active.</p>")
    else:
        empty = ("<p class='empty'>No events this far back — the ledger ends "
                 "on an earlier page.</p>")
    return (
        頭
        + 副題
        + _様式
        + "<div class='wrap ledger-events activity-ledger'>"
        "<table id='activity-table'><tr><th>When</th><th>Who</th><th>What happened</th>"
        "<th>Job</th></tr>" + 行 + "</table></div>"
        + empty
        + _頁送り(page, per, len(rows))
        # 生の帯 — 開いたままでも新しい出来事が上に差さる(1頁目だけ。語は運ばれてくる)
        + ("" if page != 0 else
           "<script>(function () {"
           "var tbl = document.getElementById('activity-table');"
           "if (!tbl) return;"
           "document.addEventListener('troupe:live', function (ev) {"
           "  (ev.detail.events || []).slice().reverse().forEach(function (e) {"
           "    var tr = document.createElement('tr');"
           "    tr.className = 'row-in';"
           "    tr.innerHTML = \"<td class='cell-when'>\" + e.at + '</td><td>' +"
           "      e.who_html + '</td><td>' + e.what + '</td>' +"
           "      \"<td class='activity-job'><a class='id' href='/detail?id=\" +"
           "      e.job_id + \"'>\" + e.head + '</a></td>';"
           "    tbl.insertBefore(tr, tbl.rows[1] || null);"
           "  });"
           "});"
           "})();</script>")
    )
