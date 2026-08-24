"""案内 — いま何をどこですればいい？（人に見えるもの §1）

問いへの答えの文字と、**画面への白名単リンクだけ**（外への誘いは文字のまま）。
答えを組むのは LLM——**押すのは人**。帳簿に書かない。

写しはここで組む——**窓が既に見せているものだけ**。案内で見えるものは増えない。
往復は画面が持ち回る（隠し欄の JSON）——帳簿に置かない。
"""

from __future__ import annotations

import json
import re as _re
from html import escape

from ui.web.hands import 手
from ui.words import 状態

#: 貼ってよい行き先。**ここに無い道は文字のまま**——LLM の吐いた URL を貼らない。
_PATHS = _re.compile(
    r"(?<![\w/])(/(?:now|day|patients|inbox|agreements|billing|fees|automations|activity|search|how"
    r"|patient\?code=[\w-]+|visit\?id=[\w-]+|detail\?id=[\w-]+))(?![\w?=&-])"
)


#: 写しに書いてよい「いま見ている頁」。白名単の外は書かない。
_見てよい道 = ("/now", "/day", "/patients", "/patient", "/inbox", "/detail", "/agreements",
              "/billing", "/fees", "/automations", "/activity", "/search", "/visit",
              "/guide", "/how")


def _写し(h: 手, viewing: str | None = None) -> str:
    """案内の材料——窓の各画面が出しているものの要約。英語（LLM への材料）。"""
    today = h.today()
    lines = [f"Date: {today}"]
    if viewing and len(viewing) < 200 and viewing.startswith(_見てよい道):
        lines.append(f"The director is currently looking at: {viewing}")

    rows = h.fetch()
    lines.append(f"\nInbox — items waiting on the director now: {len(rows)}")
    for r in rows[:8]:
        ref = f"{r.rule or (r.request_head or r.instruction)[:40]} {r.period or ''}".strip()
        extra = ("question pending" if r.question_body else
                 "assessment attached" if r.assessments else "")
        lines.append(
            f"- job {r.id}: {ref} — {状態(r.state_name)}"
            + (f" ({extra})" if extra else "")
            + f" — open /detail?id={r.id}"
        )

    拠点, 道順ごと = h.route(today)
    stops = [(who, st) for who, sts in 道順ごと.items() for st in sts]
    lines.append(f"\nToday's visits ({today}): {len(stops)}")
    for who, st in stops[:12]:
        lines.append(
            f"- {who}: {st.patient} at {st.place}, {st.purpose} — "
            f"{st.status}, prep {st.prep} — open /visit?id={st.visit_id}"
        )

    patterns = [p for p in h.patterns() if p.active_to is None]
    lines.append(f"\nRecurring visit agreements in force: {len(patterns)}")
    for p in patterns[:12]:
        every = "weekly" if p.every_weeks == "1" else f"every {p.every_weeks} weeks"
        lines.append(f"- {p.patient}: {p.weekday} {every}, {p.clinician} — {p.purpose}")

    lines.append(f"\nAutomation jobs in flight (not finished): {len(h.upcoming())}")
    lines.append(
        "\nPages: /now (the loop, live) /day (routes+visits) /inbox (decisions) "
        "/patients (incl. agreements) /billing (claims+fee schedule) "
        "/automations (rules+one-off requests) /activity /search /how"
    )
    return "\n".join(lines)


def _リンク(text: str) -> str:
    """答えの中の白名単の道だけを貼る。それ以外は文字のまま。"""
    return _PATHS.sub(lambda m: f"<a href='{m.group(1)}'>{m.group(1)}</a>", escape(text))


def 往復を読む(raw: str) -> tuple[tuple[str, str], ...]:
    """隠し欄の JSON を読む。読めなければ空——発明しない。"""
    try:
        data = json.loads(raw)
        return tuple(
            (str(q), str(a)) for q, a in data
            if isinstance(q, str) and isinstance(a, str)
        )[-3:]
    except Exception:
        return ()


#: /guide の頁だけの体裁——問いは右の吹き出しのまま、答えは紙の上の静かな段に。
#: 往復のあいだは帳簿の罫（1px の線）で切る。浮かぶ襟（ask-panel）はこの紙の外なので影響しない。
_頁の体裁 = """
<style>
.guide .guide-turn {
  margin: 0 0 10px; padding: 0 0 22px;
  border-bottom: 1px solid var(--line);
}
.guide .guide-turn:last-of-type { border-bottom: 0; }
.guide .guide-a {
  max-width: 100%; padding: 4px 0 0;
  border: 0; border-radius: 0;
}
</style>
"""


def _案内(
    question: str, answer: str, history: tuple[tuple[str, str], ...]
) -> str:
    """案内の画面。往復と、次の問いの欄。"""
    turns = "".join(
        f"<div class='guide-turn'><p class='guide-q'>{escape(q)}</p>"
        f"<div class='guide-a'>{_リンク(a)}</div></div>"
        for q, a in (*history, *(((question, answer),) if answer else ()))
    )
    carried = json.dumps(
        [*history, *(((question, answer),) if answer else ())][-3:],
        ensure_ascii=False,
    )
    empty = (
        "<p class='guide-hint'>The guide reads what this window already shows — "
        "today's route, the inbox, agreements in force, jobs in flight — and "
        "answers in text, linking only to those pages. It can point, never "
        "press. Try: <em>What needs me today?</em></p>"
        if not turns else ""
    )
    return (
        "<div class='page-head'><h1 class='page-title'>Guide</h1>"
        "<span class='page-head__aside'>Nothing asked here is written to the ledger.</span>"
        "</div>"
        "<section class='guide'>"
        + _頁の体裁
        + empty
        + turns
        + "<form method='post' action='/guide' class='guide-form'>"
        + f"<input type='hidden' name='history' value='{escape(carried, quote=True)}'>"
        + "<input class='guide-input' type='text' name='question' maxlength='500' "
          "placeholder='Ask the guide…' autofocus autocomplete='off'>"
        + "<button class='btn' type='submit'>Ask</button>"
        + "</form></section>"
    )
