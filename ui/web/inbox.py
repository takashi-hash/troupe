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
    return f"<div class='brief'>{' · '.join(組)}</div>"


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
        return "<p class='empty'>Nothing needs your judgment today.</p>"
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
        out.append(
            f"<article class='card'><div class='card__head'>"
            f"<span class='badge'>{badge}</span>"
            f"<span class='ref-name'>{escape(参照)}</span>{chip}"
            f"<span class='push sub'>due {escape(r.due)}</span></div>"
            + 患者 + 中身 + 詳細
            + f"<div class='card-actions'>{操作}</div></article>"
        )
    return "".join(out)


