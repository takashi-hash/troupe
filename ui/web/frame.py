from __future__ import annotations
from html import escape
from ui.web.style import _STYLE
from ui.words import 操作
from ui.words import 状態
from ui.words import 読める
import re as _re

_書く欄 = {"answer": "Answer", "send_back": "Reason", "abandon": "Reason"}


def _頁(
    見出し: str,
    中身: str,
    viewer: str,
    断り: str | None = None,
    notice: str | None = None,
) -> str:
    """窓の枠。**押しつけは今日だけ**——残りは引き出し（人に見えるもの §1）。

    `notice` は開示のバナー——**合成の座長が動いているあいだは、動いていると言う**。
    """
    def _tab(識別子: str) -> str:
        現在 = " aria-current='page'" if 識別子 == 見出し else ""
        return f"<a href='/{識別子}'{現在}>{escape(読める(識別子))}</a>"

    tabs = (
        "<span class='nav__label'>Care</span>"
        + "".join(_tab(t) for t in ("day", "patients"))
        + "<span class='nav__sep' role='separator'></span>"
        + "<span class='nav__label'>Back office</span>"
        + "".join(_tab(t) for t in ("inbox", "agreements", "automations", "activity", "search"))
        + "<span class='nav__sep' role='separator'></span>"
        + "<span class='nav__label'>Help</span>"
        + "".join(_tab(t) for t in ("guide", "how"))
    )
    警告 = f'<div class="refusal">{escape(断り)}</div>' if 断り else ""
    開示 = f"<div class='notice-bar'>{escape(notice)}</div>" if notice else ""
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Troupe — {escape(読める(見出し))}</title><style>{_STYLE}</style></head><body>"
        "<div class='app-shell'>"
        f"<header class='app-header'><span class='brand'>Troupe</span>"
        f"<nav class='nav' aria-label='Primary'>{tabs}</nav>"
        f"<span class='whoami'>Signed in as: <strong>{escape(viewer)}</strong></span></header>"
        f"<div class='app-content'>{開示}<main>{警告}{中身}</main></div>"
        "</div></body></html>"
    )


def _欄(組: list[tuple[str, str | None]]) -> str:
    """欄を並べる。**本文はそのまま載せる——縮めない**（人に見えるもの §2）。"""
    行 = "".join(
        f"<dt>{escape(名)}</dt><dd>{escape(値)}</dd>" for 名, 値 in 組 if 値
    )
    return f"<dl>{行}</dl>" if 行 else ""


def _押せること(押せる: tuple[str, ...], job_id: str, 戻り: str) -> str:
    """押せることを並べる。**組むのは domain の仕様**——ここは入っているものを出すだけ。"""
    階層 = {"approve": "btn btn--primary", "answer": "btn btn--primary",
            "abandon": "btn btn--destructive"}
    語感 = {"approve": "Approve", "answer": "Reply", "send_back": "Send back",
            "abandon": "Abandon"}
    out = []
    for what in 押せる:
        名 = 語感.get(what, 操作(what))
        欄 = _書く欄.get(what)
        書く = (
            f"<input type='text' name='text' aria-label='{escape(欄)}'"
            f" placeholder='{escape(欄)}' required>"
            if 欄
            else ""
        )
        確認 = (" onclick=\"return confirm('Abandon this job? This is final.')\""
                if what == "abandon" else "")
        out.append(
            f"<form class='act' method='post' action='/act'>"
            f"<input type='hidden' name='what' value='{escape(what)}'>"
            f"<input type='hidden' name='id' value='{escape(job_id)}'>"
            f"<input type='hidden' name='back' value='{escape(戻り)}'>"
            f"{書く}<button class='{階層.get(what, 'btn')}'{確認}>{escape(名)}</button></form>"
        )
    return "".join(out)


def _状態(名: str) -> str:
    return f"<span class='state'>{escape(状態(名))}</span>"



def _md(text: str) -> str:
    """最小の Markdown 描画——見出し・箇条書き・太字だけ。外の道具は使わない。"""
    out: list[str] = []
    in_list = False
    for line in text.splitlines():
        t = line.strip()
        h = _re.match(r"^(#{1,4})\s+(.*)$", t)
        if h:
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f"<p class='md-h'>{escape(h.group(2).strip('* '))}</p>")
            continue
        if _re.match(r"^[-*]\s+", t):
            if not in_list:
                out.append("<ul class='md-ul'>"); in_list = True
            out.append(f"<li>{_md_inline(t[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>"); in_list = False
        if t == "" or set(t) <= {"-", "—"}:
            continue
        out.append(f"<p>{_md_inline(t)}</p>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


def _md_inline(t: str) -> str:
    t = escape(t)
    return _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)


