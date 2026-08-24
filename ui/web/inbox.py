from __future__ import annotations
from app.dto.today_row import TodayRow
from html import escape
from ui.web.frame import _md
from ui.web.frame import _押せること
from ui.words import 状態
from urllib.parse import quote

def _帯(rows: tuple[TodayRow, ...], in_flight: int) -> str:
    """ブリーフィングの帯 — 件数と行き先だけ。**行は足さない。**

    人に見えるもの §4「先の予定は今日に載せない（赤が埋もれる）」——
    だからここに出すのは数と道案内であって、押しつけの行ではない。
    数は下に並んでいる行の集計そのもの（別の判定を持たない）。

    見た目は灰色の箱ではなく**罫線1本**——帳簿の地に、数を書いた1行が載るだけ。

    頁の頭（.page-head）もここで出す——routes が _帯 を _今日 の上に描くので、
    頭を帯の上に置くにはここしかない（見た目の正本 §2「数を先に言う」）。
    件数は len(rows) そのもの。帯は頭の直下に残る。
    """
    from ui.words import STATE_GLOSS

    def 数える(ident: str) -> int:
        return sum(1 for r in rows if STATE_GLOSS.get(r.state_name) == ident)

    承認 = 数える("AwaitingApproval")
    回答 = 数える("AwaitingAnswer")
    組 = [
        f"<strong>{承認}</strong> awaiting your approval",
        f"<strong>{回答}</strong> awaiting an answer",
        f"<strong>{in_flight}</strong> job{'s' if in_flight != 1 else ''} in flight"
        " — <a href='/automations'>automations</a>",
    ]
    頭 = (
        "<div class='page-head'><h1 class='page-title'>Inbox</h1>"
        f"<span class='count-pill'><strong>{len(rows)}</strong>"
        f" decision{'s' if len(rows) != 1 else ''} waiting</span></div>"
    )
    return 頭 + f"<p class='inbox-brief'>{' · '.join(組)}</p>"


#: /inbox だけの絞り込み。style.py（正本）には触らず、inbox- 接頭辞で**足すだけ**。
#: 広い台紙でも判断の列は ~820px に留める——判断は焦点であって、横に伸ばすものではない。
#: 判断の札の中は**箱を重ねず罫線で切る**——種別の行・題・本文・操作を髪線が分ける。
_様式 = """<style>
/* inbox — 判断の列。既存クラスの上書きは inbox- 側でだけ行う */
.inbox-queue { max-width: 820px; }
/* ブリーフィング — 箱ではなく罫線1本の行。数は等幅数字 */
.inbox-brief {
  max-width: 820px; margin: 0 0 20px; padding: 4px 0 8px;
  border-bottom: 1px solid var(--line);
  font-size: 13.5px; color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.inbox-brief strong { color: var(--ink); }
/* 判断の札 — 外枠1本だけ。中は髪線で4段に切る（種別/題/本文/操作） */
.inbox-card { padding: 0; margin-bottom: 12px; }
.inbox-card > * { margin: 0; padding: 8px 16px; }
.inbox-card > * + * { border-top: 1px solid var(--line); }
.inbox-card__kind { display: flex; align-items: center; gap: 10px; padding: 8px 16px 7px; }
.inbox-card__due {
  font-family: var(--mono); font-size: 11.5px; color: var(--muted); white-space: nowrap;
}
.inbox-card__state { margin-left: auto; }
.inbox-card__lead { padding: 9px 16px 10px; }
.inbox-card__title { display: block; font-size: 15px; font-weight: 650; line-height: 1.35; }
.inbox-card__patient { margin: 7px 0 0; }
.inbox-card__body { padding: 10px 16px 12px; }
.inbox-card__body > :first-child { margin-top: 0; }
.inbox-card .question-body, .inbox-card .draft-preview { margin-top: 8px; }
.inbox-card .fold { margin-top: 8px; }
.inbox-card .effort { font-variant-numeric: tabular-nums; }
/* 操作の段 — .card-actions の余白と線は段組み側が持つので畳む */
.inbox-card__actions {
  margin-top: 0; padding: 10px 16px 12px; justify-content: flex-end;
}
.inbox-card__actions form.act input[type=text] { flex: 0 1 180px; min-width: 0; }
/* 操作が1つ（= 回答）のときだけ、書く欄を広げる */
.inbox-card__actions form.act:only-child:has(input[type=text]) {
  flex: 1 1 auto; justify-content: flex-end;
}
.inbox-card__actions form.act:only-child input[type=text] { flex: 1 1 auto; max-width: 420px; }
</style>"""


def _参照名(r: TodayRow) -> tuple[str, str, str | None]:
    """（種類バッジ, 人間参照名, 患者記号）——UUIDの代わりに人が呼べる名。

    どの患者かは源の在りかが知っている（`db:chart/<患者記号>`）——
    配達（deliver_drafts）と同じ読みかた。ルール名から切り出さない。
    """
    if r.rule and r.source.startswith("db:chart/"):
        code = r.source.removeprefix("db:chart/").strip()
        return "Visit note", f"{code} · Visit note · {r.period or ''}".strip(), code
    if r.rule:
        return "Report", f"{r.rule} · {r.period or ''}".strip(), None
    return "Request", (r.request_head or "Request"), None


def _今日(rows: tuple[TodayRow, ...]) -> str:
    if not rows:
        return _様式 + ("<p class='empty'>Nothing needs you — "
                       "the pulse will bring the next decision here.</p>")
    out = []
    for r in rows:
        badge, 参照, code = _参照名(r)
        chip = ("<span class='chip chip--needs-answer'>⚠ Needs your answer</span>"
                if "answer" in r.actions else
                "<span class='chip chip--needs-approval'>Needs your approval</span>"
                if "approve" in r.actions else
                f"<span class='chip'>{escape(状態(r.state_name))}</span>")
        患者 = (f"<a class='patient-chip' href='/patient?code={quote(code)}'>{escape(code)} →</a>"
                if code else "")
        中身 = ""
        if r.question_body:
            中身 = f"<p class='question-body'>{escape(r.question_body)}</p>"
            if r.answer_body:
                中身 += f"<dl><dt>Answer</dt><dd>{escape(r.answer_body)}</dd></dl>"
        elif r.result_body:
            中身 = (f"<div class='draft-preview md'>{_md(r.result_body)}</div>"
                    f"<details class='fold'><summary>Show full draft</summary>"
                    f"<div class='md'>{_md(r.result_body)}</div></details>")
        見立て = "\n".join(f"{本文}（{理由}）" for 本文, 理由 in r.assessments)
        詳細 = (
            "<details class='fold'><summary>Details</summary><dl>"
            f"<dt>Brief</dt><dd>{escape(r.instruction)}</dd>"
            + (f"<dt>Source quoted</dt><dd>{escape(r.evidence_quote)}</dd>" if r.evidence_quote else "")
            + (f"<dt>Assessment</dt><dd>{escape(見立て)}</dd>" if 見立て else "")
            + (f"<dt>Recheck</dt><dd>{escape(r.recheck_at)}</dd>" if r.recheck_at else "")
            + f"<dt>AI effort</dt><dd><span class='effort'>{r.spent_calls} of {r.budget_calls}"
            f" calls · {r.spent_seconds} of {r.budget_seconds} s</span></dd>"
            f"<dt>Ledger ref</dt><dd><span class='ledger-ref'>{escape(r.id)}</span>"
            f" · <a class='link-action' href='/detail?id={quote(r.id)}'>Full history →</a></dd>"
            "</dl></details>"
        )
        操作 = _押せること(r.actions, r.id, "/inbox")
        # 4段を髪線で切る: 種別と期日と状態 → 参照名と患者への道 → 本文と引き出し → 操作。
        out.append(
            f"<article class='card inbox-card'>"
            f"<header class='inbox-card__kind'><span class='badge'>{badge}</span>"
            f"<span class='inbox-card__due'>due {escape(r.due)}</span>"
            f"<span class='inbox-card__state'>{chip}</span></header>"
            f"<div class='inbox-card__lead'>"
            f"<span class='ref-name inbox-card__title'>{escape(参照)}</span>"
            + (f"<div class='inbox-card__patient'>{患者}</div>" if 患者 else "")
            + "</div>"
            f"<div class='inbox-card__body'>{中身}{詳細}</div>"
            f"<div class='card-actions inbox-card__actions'>{操作}</div></article>"
        )
    return _様式 + f"<div class='inbox-queue'>{''.join(out)}</div>"
