"""会計の画面 — 請求の一覧・支払者への提出ファイル・患者への請求書。

すべて架空の「Nagisa Schedule」——コード・点数・支払者は発明品で、実在の制度ではない。
画面は必ずその旨を静かな1行で言う。
"""

from __future__ import annotations
from app.dto.charge_row import ChargeRow
from app.dto.claim_view import ClaimView
from html import escape
from urllib.parse import quote

#: 請求書の分類 — コード接頭辞 → 見出し。順序が表示順。
_分類表: tuple[tuple[tuple[str, ...], str], ...] = (
    (("NV", "NO"), "Home visits"),
    (("NC",), "Monthly management"),
    (("NP", "NX"), "Procedures"),
    (("ND",), "Medications"),
    (("NB",), "Materials"),
    (("NA",), "Add-ons"),
)

_診療所 = "Riverbend Home Medical Clinic"


def _隣月(month: str) -> tuple[str, str]:
    """前月と翌月 — 年月の整数演算だけで出す（日付ライブラリ不要）。"""
    年, 月 = (int(p) for p in month.split("-"))
    前年, 前月 = (年 - 1, 12) if 月 == 1 else (年, 月 - 1)
    翌年, 翌月 = (年 + 1, 1) if 月 == 12 else (年, 月 + 1)
    return f"{前年:04d}-{前月:02d}", f"{翌年:04d}-{翌月:02d}"


def _会計面(month: str, active: str) -> str:
    """Billing の2面の切り替え札 — Claims と Fee schedule。routes が両面で使う。"""
    def 札(label: str, href: str, on: bool) -> str:
        当 = " is-on' aria-current='true" if on else ""
        return f"<a class='filter-chip{当}' href='{href}'>{label}</a>"
    return (
        "<div class='filter-chips'>"
        + 札("Claims", f"/billing?month={quote(month)}", active == "claims")
        + 札("Fee schedule", f"/billing?month={quote(month)}&amp;view=fees", active == "fees")
        + "</div>"
    )


def _状態欄(c: ChargeRow, month: str, 座長の席: bool = True) -> str:
    """算定行の Status セル — 旗の行だけが琥珀のチップと裁きのフォームを持つ。"""
    if c.status == "flagged":
        if not 座長の席:
            return (
                "<span class='chip chip--needs-approval'>⚠ Needs a ruling</span>"
                f"<div class='billing-flag-reason'>{escape(c.flag_reason or '')}</div>"
                "<span class='sub'>Only the director's seat rules — switch the seat</span>"
            )
        return (
            "<span class='chip chip--needs-approval'>⚠ Needs a ruling</span>"
            f"<div class='billing-flag-reason'>{escape(c.flag_reason or '')}</div>"
            "<form method='post' action='/billing/act' class='billing-ruling'>"
            "<input type='hidden' name='what' value='resolve_charge'>"
            f"<input type='hidden' name='id' value='{escape(c.id)}'>"
            f"<input type='hidden' name='month' value='{escape(month)}'>"
            "<input name='reason' placeholder='Reason (required to allow)'>"
            "<button name='action' value='allow' class='btn btn--small'>Allow with reason</button>"
            "<button name='action' value='drop' class='btn btn--small btn--destructive'"
            " onclick=\"return confirm('Drop this line? It will bill 0.')\">Drop</button>"
            "</form>"
        )
    if c.status == "allowed":
        return f"<span class='sub'>allowed — {escape(c.resolve_reason or '')}</span>"
    if c.status == "dropped":
        return "<span class='sub'>dropped</span>"
    return "<span class='sub'>derived</span>"


def _請求札(v: ClaimView, month: str, today_month: str, 座長の席: bool = True) -> str:
    """1患者1月の請求カード — 頭に印と合計、中に算定の表、足に次の一手。"""
    確定 = v.status == "confirmed"
    印 = (
        "<span class='seal seal--signed'>CONFIRMED</span>"
        if 確定 else "<span class='seal seal--draft'>DRAFT</span>"
    )
    頭 = (
        "<div class='card__head'>"
        f"<a class='patient-chip' href='/patient?code={quote(v.patient)}'>{escape(v.patient)}</a>"
        + 印
        + f"<span class='push billing-totals num'><strong>{v.total_points:,}</strong> pts"
        f" · copay ¥{v.copay_yen:,} ({v.copay_rate}0%)</span>"
        "</div>"
        + (
            f"<p class='sub billing-confirmed-by'>confirmed by {escape(v.confirmed_by or '—')}"
            f" · {escape((v.confirmed_at or '')[:16])}</p>"
            if 確定 else ""
        )
    )
    行 = "".join(
        f"<tr{' class=billing-row--dropped' if c.status == 'dropped' else ''}>"
        f"<td class='cell-when'>{escape(c.day)}</td>"
        f"<td class='mono'>{escape(c.code)}</td>"
        f"<td>{escape(c.name)}</td>"
        f"<td class='num'>{c.qty}</td>"
        f"<td class='num'>{c.points:,}</td>"
        f"<td>{_状態欄(c, month, 座長の席)}</td></tr>"
        for c in v.charges
    )
    表 = (
        "<div class='wrap'><table class='billing-charges'>"
        "<tr><th>Day</th><th>Code</th><th>Item</th><th class='billing-th-r'>Qty</th>"
        "<th class='billing-th-r'>Points</th><th>Status</th></tr>"
        + 行 + "</table></div>"
    )
    旗あり = any(c.status == "flagged" for c in v.charges)
    if 確定:
        足 = (
            "<div class='card-actions'><a class='link-action'"
            f" href='/billing?month={quote(month)}&amp;invoice={quote(v.patient)}'>Invoice →</a></div>"
        )
    elif 旗あり:
        足 = "<div class='card-actions'><span class='sub'>Rule on the flags first</span></div>"
    elif month < today_month and not 座長の席:
        足 = ("<div class='card-actions'><span class='sub'>"
              "Only the director's seat confirms — switch the seat</span></div>")
    elif month < today_month:
        足 = (
            "<div class='card-actions'><form method='post' action='/billing/act'>"
            "<input type='hidden' name='what' value='confirm_claim'>"
            f"<input type='hidden' name='patient' value='{escape(v.patient)}'>"
            f"<input type='hidden' name='month' value='{escape(month)}'>"
            "<button class='btn btn--primary'"
            " onclick=\"return confirm('Confirm this claim? It becomes immutable.')\">"
            "Confirm and close the month</button></form></div>"
        )
    else:
        足 = "<div class='card-actions'><span class='sub'>Confirms after month end</span></div>"
    return f"<article class='card' id='claim-{escape(v.patient)}'>{頭}{表}{足}</article>"


def _右欄(
    views: tuple[ClaimView, ...], month: str, today_month: str, 座長の席: bool
) -> str:
    """座長の一瞥 — 旗の列と、確定を待つ下書きの列。行はカードの錨へ飛ぶ。"""
    旗行 = [
        "<a class='billing-rail-row' href='#claim-" + quote(v.patient) + "'>"
        f"<span class='mono billing-rail-pt'>{escape(v.patient)}</span>"
        f"<span class='mono'>{escape(c.code)}</span>"
        f"<span class='cell-when billing-rail-end'>{escape(c.day)}</span></a>"
        for v in views for c in v.charges if c.status == "flagged"
    ]
    旗塊 = (
        "<section class='billing-rail-block'>"
        "<h2 class='billing-rail-title'>Needs a ruling"
        f"<span class='count-pill'><strong>{len(旗行)}</strong></span></h2>"
        + ("".join(旗行) if 旗行
           else "<p class='sub billing-rail-empty'>No flags waiting.</p>")
        + "</section>"
    )
    if month < today_month:
        下書き = [v for v in views if v.status != "confirmed"]
        確認行 = [
            "<div class='billing-rail-row'>"
            f"<span class='mono billing-rail-pt'>{escape(v.patient)}</span>"
            f"<span class='num billing-rail-end'>{v.total_points:,} pts</span></div>"
            for v in 下書き
        ]
        確認中身 = (
            "".join(確認行) + "<p class='sub billing-rail-empty'>Confirm on each card.</p>"
            if 下書き else "<p class='sub billing-rail-empty'>No draft claims to confirm.</p>"
        )
    else:
        確認中身 = "<p class='sub billing-rail-empty'>The month confirms after it ends.</p>"
    確認塊 = (
        "<section class='billing-rail-block'>"
        "<h2 class='billing-rail-title'>Ready to confirm</h2>"
        + 確認中身 + "</section>"
    )
    席注 = (
        "" if 座長の席
        else "<p class='sub billing-rail-seat'>Only the director's seat rules"
             " — switch the seat.</p>"
    )
    return f"<aside class='page-rail'>{旗塊}{確認塊}{席注}</aside>"


def _会計(
    views: tuple[ClaimView, ...],
    month: str,
    today_month: str,
    refused: str | None = None,
    done: str | None = None,
    is_director: bool = True,
) -> str:
    """会計の頁 — その月の請求の列。旗は琥珀、確定は緑、下書きの確定は月が閉じてから。"""
    旗数 = sum(1 for v in views for c in v.charges if c.status == "flagged")
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Billing</h1>"
        f"<span class='count-pill'><strong>{len(views)}</strong> claims</span>"
        f"<span class='page-head__aside{' billing-amber' if 旗数 else ''}'>"
        f"{旗数} flagged lines · <a href='/fees'>fee schedule →</a></span>"
        "</div>"
    )
    前, 次 = _隣月(month)
    月帯 = (
        "<div class='day-bar billing-monthbar'><span class='day-nav'>"
        f"<a href='/billing?month={前}'>← {前}</a>"
        f" · <strong>{escape(month)}</strong> · "
        f"<a href='/billing?month={次}'>{次} →</a>"
        "</span></div>"
    )
    帯 = (
        (f"<div class='refusal'>{escape(refused)}</div>" if refused else "")
        + (f"<div class='banner banner--success'>✓ {escape(done)}</div>" if done else "")
    )
    if not views:
        本体 = (
            "<p class='empty'>Charges derive from signed visits"
            " — none are signed yet this month.</p>"
        )
    else:
        確定あり = any(v.status == "confirmed" for v in views)
        提出行 = (
            "<p class='billing-filelink'><a class='link-action'"
            f" href='/billing?month={quote(month)}&amp;view=file'>Submission file →</a></p>"
            if 確定あり else ""
        )
        本体 = 提出行 + "".join(_請求札(v, month, today_month, is_director) for v in views)
    return (
        頭 + _会計面(month, "claims")
        + "<div class='page-cols'><div class='page-main'>"
        + 月帯 + 帯 + 本体
        + "</div>"
        + _右欄(views, month, today_month, is_director)
        + "</div>"
        + "<p class='sub billing-fictional'>Nagisa Schedule — every code, point value and payer"
        " on this page is invented; no real billing system is involved.</p>"
        # この頁だけの化粧 — 正本の style は触らない
        + "<style>"
        # 2列 — 左が帳簿、右が座長の一瞥。狭ければ右欄は下に積む(消さない)
        ".page-cols { display: grid; grid-template-columns: minmax(0,1fr) 340px;"
        " gap: 28px; align-items: start; }"
        ".page-rail { position: sticky; top: 20px; }"
        "@media (max-width: 1100px) { .page-cols { display: block; }"
        " .page-rail { position: static; margin-top: 24px; } }"
        # 右欄の塊は札1段・中は罫線の行(帳簿の作法)
        ".billing-rail-block { border: 1px solid var(--line); border-radius: var(--r-md);"
        " padding: 12px 16px 10px; margin-bottom: 14px; background: Canvas; }"
        ".billing-rail-title { display: flex; align-items: baseline; gap: 8px; margin: 0 0 4px;"
        " font-size: 11.5px; font-weight: 650; letter-spacing: .07em;"
        " text-transform: uppercase; color: var(--muted); }"
        ".billing-rail-row { display: flex; align-items: baseline; gap: 8px;"
        " padding: 6.5px 0; border-top: 1px solid var(--line);"
        " font-size: 13px; text-decoration: none; }"
        "a.billing-rail-row:hover { background: var(--faint); }"
        ".billing-rail-pt { font-weight: 600; }"
        ".billing-rail-end { margin-left: auto; text-align: right;"
        " font-variant-numeric: tabular-nums; }"
        ".billing-rail-empty { margin: 4px 0 2px; }"
        ".billing-rail-seat { margin: 0 2px; }"
        # 金の列は右寄せ・等幅数字。刻みは 4px の格子(帳簿を目で走る密度)
        ".billing-monthbar { font-variant-numeric: tabular-nums; }"
        ".billing-charges td { padding: 8px 12px; }"
        ".billing-charges td.num, .billing-th-r { text-align: right; }"
        ".billing-amber { color: color-mix(in srgb, var(--warn) 70%, CanvasText); font-weight: 600; }"
        ".billing-totals { font-size: 13.5px; }"
        ".billing-confirmed-by { margin: -2px 0 10px; }"
        ".billing-flag-reason { font-size: 12.5px; white-space: normal; max-width: 46ch;"
        " color: color-mix(in srgb, var(--warn) 70%, CanvasText); margin: 4px 0 6px; }"
        ".billing-ruling { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }"
        ".billing-ruling input[name=reason] { width: 200px; max-width: 100%;"
        " font-size: 13px; padding: 4px 9px; }"
        ".billing-row--dropped td { color: var(--muted); }"
        ".billing-row--dropped td:nth-child(3) { text-decoration: line-through; }"
        ".billing-filelink { margin: 0 0 14px; }"
        ".billing-fictional { margin-top: 26px; }"
        "</style>"
    )


def _提出ファイル(views: tuple[ClaimView, ...], month: str) -> str:
    """支払者への提出ファイル — 確定した請求だけを、実物の UKE を映した架空のレコード型式で。"""
    確定 = tuple(v for v in views if v.status == "confirmed")
    下書き数 = len(views) - len(確定)
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Submission file</h1>"
        f"<span class='count-pill'><strong>{len(確定)}</strong> confirmed claims</span>"
        "<span class='page-head__aside'>"
        f"<a href='/billing?month={quote(month)}'>← Billing {escape(month)}</a></span>"
        "</div>"
        "<p class='page-sub'>Nagisa Claims Bureau (fictional) — record-type text mirroring"
        " the real UKE shape; every value invented.</p>"
    )
    if not 確定:
        return 頭 + (
            f"<p class='empty'>No confirmed claims in {escape(month)} — nothing to submit.</p>"
        )
    総点 = sum(v.total_points for v in 確定)
    行 = [f"IR|{_診療所}|NAGISA-0001|{month}|{len(確定)}|{総点}"]
    for v in 確定:
        行.append(f"RE|{v.patient}|{month}|{v.copay_rate}0%|{v.total_points}")
        for c in v.charges:
            # 落とした行・旗の行はファイルに載らない(0点で請求しない)
            if c.status in ("dropped", "flagged"):
                continue
            行.append(f"SI|{c.day}|{c.code}|{c.name}|{c.qty}|{c.points}")
    行.append(f"GO|{len(確定)}|{総点}")
    注 = (
        f"<p class='sub'>Draft claims are not in the file — {下書き数} draft claims"
        " remain this month.</p>"
        if 下書き数 else ""
    )
    return (
        頭
        + f"<pre class='billing-file'>{escape(chr(10).join(行))}</pre>"
        + 注
        + "<style>"
        ".billing-file { font-family: var(--mono); font-size: 12.5px; line-height: 1.7;"
        " font-variant-numeric: tabular-nums;"
        " background: var(--faint); border: 1px solid var(--line);"
        " border-radius: var(--r-md);"
        " padding: 14px 18px; overflow-x: auto; margin: 0 0 14px; }"
        "</style>"
    )


def _分類名(code: str) -> str:
    for 接頭たち, 名 in _分類表:
        if code.startswith(接頭たち):
            return 名
    return "Other"


def _請求書(view: ClaimView, month: str) -> str:
    """患者への請求書 — 印刷向けの明細。落とした行・旗の行は載らない。ボタンは置かない。"""
    頭 = (
        f"<div class='page-head'><h1 class='page-title'>Invoice — {escape(view.patient)}</h1>"
        "<span class='page-head__aside billing-back'>"
        f"<a href='/billing?month={quote(month)}'>← Billing</a></span></div>"
        f"<p class='billing-clinic'>{_診療所}</p>"
        f"<p class='sub'>Billing month {escape(month)}</p>"
    )
    有効 = tuple(c for c in view.charges if c.status not in ("dropped", "flagged"))
    組: dict[str, list[ChargeRow]] = {}
    for c in 有効:
        組.setdefault(_分類名(c.code), []).append(c)
    行々: list[str] = []
    for 名 in [名 for _, 名 in _分類表] + ["Other"]:
        if 名 not in 組:
            continue
        行々.append(f"<tr class='billing-cat'><td colspan='5'>{名}</td></tr>")
        for c in 組[名]:
            行々.append(
                f"<tr><td class='cell-when'>{escape(c.day)}</td>"
                f"<td class='mono'>{escape(c.code)}</td>"
                f"<td>{escape(c.name)}</td>"
                f"<td class='num'>{c.qty}</td>"
                f"<td class='num'>{c.points:,}</td></tr>"
            )
        小計 = sum(c.points for c in 組[名])
        行々.append(
            f"<tr class='billing-subtotal'><td colspan='4'>Subtotal — {名}</td>"
            f"<td class='num'>{小計:,}</td></tr>"
        )
    表 = (
        "<div class='wrap'><table class='billing-lines'>"
        "<tr><th>Day</th><th>Code</th><th>Item</th><th class='billing-th-r'>Qty</th>"
        "<th class='billing-th-r'>Points</th></tr>"
        + "".join(行々) + "</table></div>"
        if 有効 else "<p class='sub'>No billable lines this month.</p>"
    )
    合計 = (
        "<dl class='billing-sums'>"
        f"<dt>Total points</dt><dd class='num'>{view.total_points:,}</dd>"
        f"<dt>Total</dt><dd class='num'>¥{view.total_points * 10:,}</dd>"
        f"<dt>Copay rate</dt><dd>{view.copay_rate}0%</dd>"
        "</dl>"
        f"<p class='billing-due'>Amount due <strong class='num'>¥{view.copay_yen:,}</strong></p>"
    )
    return (
        "<div class='billing-invoice'>"
        + 頭 + 表 + 合計
        + "<p class='sub billing-fictional'>Itemized statement per the (fictional) rules"
        " — all invented.</p>"
        + "</div>"
        + "<style>"
        ".billing-invoice { max-width: 760px; }"
        ".billing-clinic { font-size: 15px; font-weight: 650; margin: 2px 0 2px; }"
        # 金の列は右寄せ・等幅数字。分類は塗りの帯でなく、罫線の小見出し
        ".billing-lines td { padding: 8px 12px; }"
        ".billing-lines td.num, .billing-th-r { text-align: right; }"
        ".billing-cat td { padding: 18px 12px 4px; font-size: 11px; font-weight: 650;"
        " letter-spacing: .09em; text-transform: uppercase; color: var(--muted);"
        " border-bottom: 1px solid var(--line-strong); }"
        "tr.billing-cat:hover { background: none; }"
        ".billing-subtotal td { font-weight: 600; border-bottom: 1px solid var(--line-strong); }"
        ".billing-subtotal td:first-child { text-align: right; color: var(--muted);"
        " font-weight: 500; }"
        # 合計の塊は帳簿の作法で右下へ。総額は太い罫の上、記録の書体で
        ".billing-sums { margin: 18px 0 0 auto; max-width: 320px; }"
        ".billing-sums dd { text-align: right; font-variant-numeric: tabular-nums; }"
        ".billing-due { display: flex; justify-content: space-between;"
        " align-items: baseline; gap: 16px; max-width: 320px;"
        " margin: 12px 0 6px auto; padding-top: 10px;"
        " border-top: 1px solid var(--line-strong); font-size: 14px; }"
        ".billing-due strong { font-family: var(--serif); font-size: 26px;"
        " font-weight: 600; }"
        ".billing-fictional { margin-top: 26px; }"
        "@media print { .billing-back { display: none !important; } }"
        "</style>"
    )
