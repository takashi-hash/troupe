"""点数表の頁 — Nagisa Schedule の参照一覧（読むだけ・押すものが無い頁）。

**全部架空**——コード・点数・支払者まで発明。実在の点数表の構造だけを写す。
種別ごとに束ねて並べる: 訪問/臨時 → 月次 → 行為 → 薬剤 → 材料 → 加算。
"""

from __future__ import annotations
from app.dto.fee_row import FeeRow
from html import escape

#: 種別ごとの束と並び順 — 訪問・臨時が先頭、加算が最後。
_束 = (
    ("Visits & on-call", ("visit", "oncall")),
    ("Monthly management", ("monthly",)),
    ("Acts", ("act",)),
    ("Drugs", ("drug",)),
    ("Materials", ("material",)),
    ("Add-ons", ("addon",)),
)

#: 種別 → badge の表示語。
_種別札 = {
    "visit": "Visit",
    "oncall": "On-call",
    "monthly": "Monthly",
    "act": "Act",
    "drug": "Drug",
    "material": "Material",
    "addon": "Add-on",
}

#: 算定単位 → 人が読む言い方。
_単位 = {
    "per_visit": "per visit",
    "per_event": "per event",
    "per_day": "per day",
    "per_week": "per week",
    "per_month": "once a month",
    "per_quarter": "once per 3 months",
}


def _点か円(r: FeeRow) -> str:
    """点数の行は「800 pts」、円建て（薬剤・材料）は換算待ちの円を見せる。"""
    if r.points is not None:
        return f"<span class='num'><strong>{r.points}</strong> pts</span>"
    return (
        f"<span class='num'>¥{escape(r.price_yen or '—')}</span>"
        " <span class='fees-derive'>→ points at derivation</span>"
    )


def _一行(r: FeeRow) -> str:
    上限 = f"{r.weekly_cap} / week" if r.weekly_cap is not None else "—"
    return (
        f"<tr><td class='mono'>{escape(r.code)}</td>"
        f"<td>{escape(r.name)}</td>"
        f"<td><span class='badge'>{escape(_種別札.get(r.kind, r.kind))}</span></td>"
        f"<td>{_点か円(r)}</td>"
        f"<td>{escape(_単位.get(r.unit, r.unit.replace('_', ' ')))}</td>"
        f"<td class='num'>{上限}</td>"
        f"<td class='fees-note'>{escape(r.note) if r.note else '—'}</td></tr>"
    )


def _点数表(rows: tuple[FeeRow, ...]) -> str:
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Fee schedule</h1>"
        f"<span class='count-pill'><strong>{len(rows)}</strong> items</span>"
        "<span class='page-head__aside'>Nagisa Schedule — every value invented</span>"
        "</div>"
    )
    if not rows:
        return 頭 + "<p class='empty'>The fee master is empty — nothing to price against.</p>"

    説明 = (
        "<p class='fees-intro'>Drugs convert to points at derivation: a unit priced"
        " ¥15 or less counts as 1 point, anything above is yen ÷ 10 rounded by the"
        " go-sha-go-cho-nyu rule (a fraction of 0.5 or below drops, above 0.5 rounds up)."
        " Materials convert as yen ÷ 10 rounded half-up.</p>"
    )

    # 束ごとに区切り行を挟んで並べる。表に無い種別が来ても落とさず末尾に足す
    本体: list[str] = []
    済み: set[str] = set()
    for 見出し, 種別たち in _束:
        組 = [r for r in rows if r.kind in 種別たち]
        済み.update(種別たち)
        if 組:
            本体.append(f"<tr class='fees-group'><td colspan='7'>{見出し}</td></tr>")
            本体.extend(_一行(r) for r in 組)
    残り = [r for r in rows if r.kind not in 済み]
    if 残り:
        本体.append("<tr class='fees-group'><td colspan='7'>Other</td></tr>")
        本体.extend(_一行(r) for r in 残り)

    return (
        頭
        + 説明
        + "<div class='wrap'><table>"
        "<tr><th>Code</th><th>Item</th><th>Kind</th><th>Points / Price</th>"
        "<th>Unit</th><th>Cap</th><th>Note</th></tr>"
        + "".join(本体)
        + "</table></div>"
        # この頁だけの見た目 — 区切り行は静かな小見出し、換算注記は脇の声
        "<style>"
        ".fees-intro { font-size: 13.5px; color: var(--muted); max-width: 78ch;"
        " margin: 0 0 18px; }"
        "tr.fees-group td { padding: 20px 12px 5px; font-size: 11px; font-weight: 650;"
        " letter-spacing: .09em; text-transform: uppercase; color: var(--muted);"
        " border-bottom: 1px solid var(--line-strong); }"
        "tr.fees-group:hover { background: none; }"
        ".fees-derive { font-size: 12px; color: var(--muted); white-space: nowrap; }"
        ".fees-note { color: var(--muted); font-size: 13px; }"
        "</style>"
    )
