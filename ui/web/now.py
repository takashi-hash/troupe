"""いま — この座はいま動いているのか？（人に見えるもの §1）

環のいま——説明(/how §01)の環の図が、生きた数で動く。
段を押すと説明の文がその場に出る。**予告はしない——起きた事実だけ。**
生の帯は /events(SSE)が運ぶ——器が同じ読みを繰り返すだけ。
"""

from __future__ import annotations

import json
from html import escape

from app.dto.history_row import HistoryRow
from app.dto.now_view import NowView
from ui.web.activity import _誰
from ui.words import 出来事

#: 段の説明——/how §01 の文そのまま(言い換えない)。押した段の下に出る。
_段の文 = {
    "clock": ("The clock", "It creates jobs from your automation rules and the calendar, "
              "hands them out, checks results, and plans visits from recurring agreements. "
              "It never judges."),
    "ai": ("The AI", "Gemini, running as a worker named Nomi, arrives uncalled — the clock "
           "never wakes it. It picks up a job, reads its source, and either submits a result "
           "with evidence, asks you a question, or reports that it is stuck."),
    "check": ("The machine check", "Before anything reaches you, the result is checked "
              "against the rule's acceptance terms — evidence quoted, required terms "
              "present. What fails is sorted, not shown."),
    "you": ("You", "The only things a machine is never allowed to do: approve, send back, "
            "answer, abandon — and sign. A note becomes the record only when a human "
            "signs it."),
}


def _帯の行(r: HistoryRow) -> str:
    """生の帯の1行。SSE で足す行と同じ形——鋳型は下の JS にもある(語は運ばれてくる)。"""
    return (
        f"<div class='now-evt'><span class='now-evt__at num'>{escape(r.at[-5:])}</span>"
        + _誰(r.by, r.by_kind)
        + f"<span class='now-evt__what'>{escape(出来事(r.what))}</span>"
        f"<a class='now-evt__head' href='/detail?id={escape(r.job_id)}'>{escape(r.head)}</a></div>"
    )


def _段(鍵: str, 名: str, 副: str, 数: int, 数の印: str, 帯色: str = "") -> str:
    # 中身のある段は生きて見える(busy)——数が0なら静か。嘘の点滅はしない
    busy = " is-busy" if 数 else ""
    return (
        f"<button type='button' class='loop-stage{帯色}{busy}' data-stage='{鍵}'>"
        f"<span class='loop-stage__name'>{escape(名)}</span>"
        f"<span class='loop-stage__sub'><span class='loop-stage__pip'></span>"
        f"{escape(副)}</span>"
        f"<span class='loop-stage__n num' data-now='{数の印}'>{数}</span></button>"
    )


def _いま(v: NowView, 帯: tuple[HistoryRow, ...]) -> str:
    """いまの画面。環の図がヒーロー——数は全部本物、動きは出来事が起こす。"""
    合計 = v.queued + len(v.working) + v.checking + v.waiting
    脈 = (f"last pulse <span class='num' data-now='beat'>{escape(v.beat_at[-5:])}</span>"
          if v.beat_at else "<span data-now='beat'>no pulse yet</span>")
    作業中 = "".join(
        f"<div class='now-working__item'><a href='/detail?id={escape(id)}'>{escape(head)}</a>"
        "<span class='now-working__dot'></span></div>"
        for id, head in v.working
    ) or ("<p class='sub' data-now-empty>Nothing is being worked on this second — "
          "the next pulse may change that.</p>")
    説明 = json.dumps({k: {"name": n, "text": t} for k, (n, t) in _段の文.items()})
    return (
        "<div class='page-head'><h1 class='page-title'>Now</h1>"
        f"<span class='count-pill'><strong data-now='total'>{合計}</strong> in flight</span>"
        f"<span class='page-head__aside'>{脈} · two pulses every 60s</span></div>"
        "<p class='page-sub'>The loop, live — every number is read from the ledger this "
        "second. Press a stage to see what it is allowed to do.</p>"

        # ---- 環(ヒーロー) — /how §01 の図が生きた数で動く ----
        "<section class='loop' aria-label='The loop, live'>"
        + _段("clock", "The clock", "creates & hands out", v.queued, "queued")
        + f"<span class='loop-link{' has-flow' if v.queued else ''}' data-link='queued' aria-hidden='true'></span>"
        + _段("ai", "The AI — Nomi",
              "consulting Gemini…" if v.working else "reads the source · asks Gemini",
              len(v.working), "working", " loop-stage--ai")
        + f"<span class='loop-link{' has-flow' if v.working else ''}' data-link='working' aria-hidden='true'></span>"
        + _段("check", "The machine check", "evidence quoted? terms present?", v.checking, "checking")
        + f"<span class='loop-link{' has-flow' if v.checking else ''}' data-link='checking' aria-hidden='true'></span>"
        + _段("you", "You", "approve · answer · sign", v.waiting, "waiting", " loop-stage--you")
        + "</section>"
        "<p class='loop-note' id='stage-note' hidden></p>"

        # ---- 下段: 作業中 | 生の帯 | 人待ち ----
        "<div class='now-cols'>"
        "<section class='now-col'><h3 class='now-col__head'>Working now</h3>"
        f"<div id='now-working'>{作業中}</div></section>"
        "<section class='now-col now-col--feed'><h3 class='now-col__head'>Live ledger</h3>"
        f"<div id='now-feed'>{''.join(_帯の行(r) for r in 帯)}</div>"
        "<p class='sub'>Nothing is overwritten — the ledger can always answer "
        "\"what happened, and who decided it.\" <a href='/activity'>Full ledger →</a></p>"
        "</section>"
        "<section class='now-col'><h3 class='now-col__head'>Waiting for you</h3>"
        f"<div class='now-waiting{' now-waiting--some' if v.waiting else ''}'>"
        f"<span class='now-waiting__n num' data-now='waiting2'>{v.waiting}</span>"
        f"<span class='now-waiting__word'>decision{'' if v.waiting == 1 else 's'}</span></div>"
        "<p class='sub'><a href='/inbox'>Open the inbox →</a> — approving, answering and "
        "signing never leave a human's hands.</p></section>"
        "</div>"

        # ---- 裾の細字 — 旧 /how の残り。畳んで置く(開けば全文・頁は一枚に収まる) ----
        "<footer class='now-fine'><details class='fold'>"
        "<summary>The fine print — what the AI cannot do · the color grammar · "
        "where this runs</summary>"
        "<p>By construction, not by policy: the AI cannot approve its own work — no code "
        "path exists from the agent to approval. It cannot sign a medical record, or touch "
        "one that is signed. It reads only <em>signed</em> notes — its own unsigned drafts "
        "are never its source. Its word is never evidence — a result must quote the source, "
        "or the clock sends it back. It stops at its budget. The "
        "<a href='/guide'>guide</a> holds no writing tools at all — it can point at a page, "
        "and nothing else.</p>"
        "<p>Only four buttons in the whole product are ever filled solid — "
        "<strong>Sign</strong>, <strong>Approve</strong>, <strong>Reply</strong>, "
        "<strong>Confirm</strong> — the heaviest human judgments. Green means signed or "
        "passed, amber means a human is needed, red is destructive or expired, blue is "
        "information, gray is inert.</p>"
        "<p>Cloud Scheduler fires two Cloud Run Jobs every 60 seconds; this window is a "
        "Cloud Run service; the ledger and the synthetic EMR are Cloud SQL for PostgreSQL; "
        "the model is Gemini via Vertex AI, reached with the workload's own identity — "
        "no API key exists anywhere. Every patient, address and clinician is invented; "
        "patient homes are stood in by public landmarks.</p>"
        "</details></footer>"

        # ---- 器のJS: 段の説明・SSEの反映(語は全部サーバーから届く) ----
        f"<script>(function () {{"
        f"var TEXTS = {説明};"
        """
var note = document.getElementById('stage-note');
document.querySelectorAll('.loop-stage').forEach(function (b) {
  b.addEventListener('click', function () {
    var t = TEXTS[b.dataset.stage];
    note.innerHTML = '<strong>' + t.name + '.</strong> ' + t.text;
    note.hidden = false;
  });
});
function setNum(el, v) {
  if (!el) return;
  var s = String(v);
  if (el.textContent === s) return;
  el.textContent = s;
  el.classList.remove('tick'); void el.offsetWidth; el.classList.add('tick');
}
document.addEventListener('troupe:live', function (ev) {
  var d = ev.detail;
  var counts = {queued: d.queued, working: d.working.length,
                checking: d.checking, waiting: d.waiting};
  document.querySelectorAll('.loop-stage').forEach(function (s) {
    var key = {clock: 'queued', ai: 'working', check: 'checking', you: 'waiting'}[s.dataset.stage];
    var busy = (counts[key] || 0) > 0;
    s.classList.toggle('is-busy', busy);
    if (s.dataset.stage === 'ai') {
      var sub = s.querySelector('.loop-stage__sub');
      var text = busy ? 'consulting Gemini…' : 'reads the source · asks Gemini';
      if (sub && sub.lastChild) sub.lastChild.textContent = text;
    }
  });
  document.querySelectorAll('.loop-link').forEach(function (l) {
    l.classList.toggle('has-flow', (counts[l.dataset.link] || 0) > 0);
  });
  ['queued', 'checking', 'waiting'].forEach(function (k) {
    setNum(document.querySelector("[data-now='" + k + "']"), d[k]);
  });
  setNum(document.querySelector("[data-now='waiting2']"), d.waiting);
  setNum(document.querySelector("[data-now='total']"),
         d.queued + d.working.length + d.checking + d.waiting);
  setNum(document.querySelector("[data-now='working']"), d.working.length);
  if (d.beat_at) {
    setNum(document.querySelector("[data-now='beat']"), d.beat_at.slice(-5));
  }
  var box = document.getElementById('now-working');
  if (box && d.working) {
    box.innerHTML = d.working.length
      ? d.working.map(function (w) {
          return "<div class='now-working__item'><a href='/detail?id=" + w[0] + "'>" +
            w[1] + "</a><span class='now-working__dot'></span></div>";
        }).join('')
      : "<p class='sub'>Nothing is being worked on this second.</p>";
  }
  var feed = document.getElementById('now-feed');
  (d.events || []).slice().reverse().forEach(function (e) {
    var row = document.createElement('div');
    row.className = 'now-evt row-in';
    row.innerHTML = "<span class='now-evt__at num'>" + e.at.slice(-5) + "</span>" +
      e.who_html + "<span class='now-evt__what'>" + e.what + "</span>" +
      "<a class='now-evt__head' href='/detail?id=" + e.job_id + "'>" + e.head + "</a>";
    feed.prepend(row);
    var lit = {clock: 'clock', agent: 'ai', human: 'you'}[e.by_kind];
    var st = lit && document.querySelector(".loop-stage[data-stage='" + lit + "']");
    if (st) { st.classList.remove('is-lit'); void st.offsetWidth; st.classList.add('is-lit'); }
    while (feed.children.length > 20) feed.removeChild(feed.lastChild);
  });
});
})();</script>"""
    )
