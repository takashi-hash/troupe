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
        + "".join(_tab(t) for t in ("inbox", "agreements", "billing", "fees", "automations", "activity", "search"))
        + "<span class='nav__sep' role='separator'></span>"
        + "<span class='nav__label'>Help</span>"
        + "".join(_tab(t) for t in ("guide", "how"))
    )
    警告 = f'<div class="refusal">{escape(断り)}</div>' if 断り else ""
    開示 = f"<div class='notice-bar'>{escape(notice)}</div>" if notice else ""
    # 案内の襟 — /guide の頁そのものには重ねない(あちらが正面玄関)
    襟 = _案内の襟() if 見出し != "guide" else ""
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Troupe — {escape(読める(見出し))}</title><style>{_STYLE}</style></head><body>"
        "<div class='app-shell'>"
        "<header class='app-header'>"
        "<a class='brand' href='/day'><span class='pulse-dot'></span>Troupe</a>"
        "<span class='brand-sub'>two pulses · every 60s</span>"
        f"<nav class='nav' aria-label='Primary'>{tabs}</nav>"
        f"<span class='whoami'>Signed in as: <strong>{escape(viewer)}</strong></span></header>"
        f"<div class='app-content'>{開示}<main>{警告}<div class='paper'>{中身}</div></main></div>"
        f"</div>{襟}</body></html>"
    )


def _案内の襟() -> str:
    """右下の襟と札。往復は sessionStorage——帳簿に書かない。JS が無ければ /guide が受ける。"""
    return (
        "<a id='ask-launcher' class='ask-launcher' href='/guide'>"
        "<span class='pulse-dot'></span>Ask</a>"
        "<section id='ask-panel' class='ask-panel' aria-label='Guide'>"
        "<div class='ask-panel__head'><span class='pulse-dot'></span>Guide"
        "<small>&nbsp;— can point, never press</small>"
        "<button class='ask-panel__close' type='button' aria-label='Close'>&times;</button></div>"
        "<div class='ask-panel__log'><div class='ask-suggest'>"
        "<button type='button'>What needs me today?</button>"
        "<button type='button'>Why is this job stuck?</button>"
        "<button type='button'>Anything unsigned this week?</button>"
        "</div></div>"
        "<form class='ask-panel__form'>"
        "<input type='text' name='question' maxlength='500' "
        "placeholder='Ask the guide…' autocomplete='off'>"
        "<button class='btn btn--small' type='submit'>Ask</button></form>"
        "<p class='ask-panel__note'>Answers come only from what this window already shows."
        " Full page: <a href='/guide'>/guide</a></p>"
        "</section>"
        "<script>" + _襟のJS + "</script>"
    )


#: 襟の JS — 取ってくる・積む・覚える(sessionStorage)。これ以外の動きは持たない。
_襟のJS = """
(function(){
var KEY='troupe-guide-history';
var panel=document.getElementById('ask-panel'),launcher=document.getElementById('ask-launcher');
if(!panel||!launcher)return;
var log=panel.querySelector('.ask-panel__log'),form=panel.querySelector('form'),
    input=form.querySelector('input[name=question]');
function hist(){try{var h=JSON.parse(sessionStorage.getItem(KEY)||'[]');return Array.isArray(h)?h:[];}catch(e){return[];}}
function save(h){sessionStorage.setItem(KEY,JSON.stringify(h.slice(-3)));}
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function turn(q,aHtml){var el=document.createElement('div');el.className='guide-turn';
el.innerHTML="<p class='guide-q'>"+esc(q)+"</p><div class='guide-a'>"+aHtml+"</div>";
log.appendChild(el);log.scrollTop=log.scrollHeight;return el;}
function render(){log.querySelectorAll('.guide-turn').forEach(function(n){n.remove()});
hist().forEach(function(t){turn(t[0],esc(t[1]));});}
panel.querySelectorAll('.ask-suggest button').forEach(function(b){
b.addEventListener('click',function(){input.value=b.textContent;form.requestSubmit();});});
launcher.addEventListener('click',function(e){e.preventDefault();
panel.classList.toggle('is-open');
if(panel.classList.contains('is-open')){render();input.focus();}});
panel.querySelector('.ask-panel__close').addEventListener('click',function(){
panel.classList.remove('is-open');});
form.addEventListener('submit',function(e){e.preventDefault();
var q=input.value.trim();if(!q)return;
var sug=panel.querySelector('.ask-suggest');if(sug)sug.remove();
input.value='';input.disabled=true;
var el=turn(q,'');
var think=document.createElement('p');think.className='ask-thinking';
think.textContent='The guide is reading the ledger…';
log.appendChild(think);log.scrollTop=log.scrollHeight;
var fd=new FormData();fd.append('question',q);
fd.append('history',JSON.stringify(hist()));
fd.append('path',location.pathname+location.search);
fetch('/guide/turn',{method:'POST',body:fd})
.then(function(r){return r.json();})
.then(function(d){think.remove();
el.querySelector('.guide-a').innerHTML=d.answer_html;
var h=hist();h.push([q,d.answer_text]);save(h);})
.catch(function(){think.textContent='The guide could not answer just now.';})
.finally(function(){input.disabled=false;input.focus();log.scrollTop=log.scrollHeight;});});
})();
"""


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


