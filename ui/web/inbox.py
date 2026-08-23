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
    return f"<div class='brief inbox-brief'>{' · '.join(組)}</div>"


#: /inbox だけの絞り込み。style.py（正本）には触らず、inbox- 接頭辞で**足すだけ**。
#: 広い台紙でも判断の列は ~820px に留める——判断は焦点であって、横に伸ばすものではない。
_様式 = """<style>
/* inbox — 判断の列。既存クラスの上書きは inbox- 側でだけ行う */
.inbox-queue, .brief.inbox-brief { max-width: 820px; }
.inbox-card { padding: 14px 18px 12px; margin-bottom: 12px; }
.inbox-card__head { display: flex; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.inbox-card__lead { flex: 1 1 260px; min-width: 0; }
.inbox-card__kind { display: flex; align-items: baseline; gap: 10px; margin: 0 0 5px; }
.inbox-card__due {
  font-family: var(--mono); font-size: 11.5px; color: var(--muted); white-space: nowrap;
}
.inbox-card__title { display: block; font-size: 15px; font-weight: 650; line-height: 1.35; }
.inbox-card__patient { margin: 7px 0 0; }
.inbox-card__state { flex: none; margin-left: auto; }
.inbox-card .question-body, .inbox-card .draft-preview { margin-top: 8px; }
.inbox-card .fold { margin-top: 8px; }
.inbox-card__actions { margin-top: 12px; padding-top: 10px; justify-content: flex-end; }
.inbox-card__actions form.act input[type=text] { flex: 0 1 180px; min-width: 0; }
/* 操作が1つ（= 回答）のときだけ、書く欄を広げる */
.inbox-card__actions form.act:only-child:has(input[type=text]) {
  flex: 1 1 auto; justify-content: flex-end;
}
.inbox-card__actions form.act:only-child input[type=text] { flex: 1 1 auto; max-width: 420px; }
</style>"""


def _参照名(r: TodayRow) -> tuple[str, str, str | None]:
    """（種類バッジ, 人間参照名, 患者記号）——UUIDの代わりに人が呼べる名。"""
    if r.rule and r.rule.startswith("Visit Note Draft"):
        code = r.rule.rsplit("— ", 1)[-1].strip()
        return "Visit note", f"{code} · Visit note · {r.period or ''}".strip(), code
    if r.rule:
        return "Report", f"{r.rule} · {r.period or ''}".strip(), None
    return "Request", (r.request_head or "Request"), None


def _今日(rows: tuple[TodayRow, ...]) -> str:
    if not rows:
        return _様式 + "<p class='empty'>Nothing needs your judgment today.</p>"
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
        # 階層は3段: 種類と期日（小・上）→ 参照名（題）→ 患者への道。状態チップは右肩。
        out.append(
            f"<article class='card inbox-card'><header class='inbox-card__head'>"
            f"<div class='inbox-card__lead'>"
            f"<div class='inbox-card__kind'><span class='badge'>{badge}</span>"
            f"<span class='inbox-card__due'>due {escape(r.due)}</span></div>"
            f"<span class='ref-name inbox-card__title'>{escape(参照)}</span>"
            + (f"<div class='inbox-card__patient'>{患者}</div>" if 患者 else "")
            + f"</div><span class='inbox-card__state'>{chip}</span></header>"
            + 中身 + 詳細
            + f"<div class='card-actions inbox-card__actions'>{操作}</div></article>"
        )
    return _様式 + f"<div class='inbox-queue'>{''.join(out)}</div>"


