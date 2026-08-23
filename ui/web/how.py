"""説明 — この仕組みは何がどう動く？（人に見えるもの §1）

環の図・登場人物・色の語彙・**AI にできないこと**。静的——**集める操作は無い**。
"""

from __future__ import annotations


def _説明() -> str:
    # 頭は頁の決まり（style.py §2）——静的な頁なので数える物は無く、件数札は出さない。
    # 体裁は「綴じた文書」——5枚の枠札をやめ、章は見出しと罫線で切る（紙の上に紙を重ねない）。
    # 文は監査済み——並べ替えてよいが、事実の文言は変えない。
    return """
<div class='page-head'><h1 class='page-title'>How Troupe works</h1></div>
<section class='how'>
<style>
.how .page-sub { margin: 0 0 4px; }
.how-sec { margin: 34px 0 0; }
.how-sec > h2 {
  font-family: var(--serif); font-size: 18px; font-weight: 600;
  margin: 0 0 12px; padding: 0 0 7px;
  border-bottom: 1px solid var(--line);
}
.how-no {
  font-family: var(--mono); font-size: 12px; font-weight: 400;
  color: var(--muted); margin-right: 12px;
  font-variant-numeric: tabular-nums; letter-spacing: .05em;
}
.how p { max-width: 68ch; }
.how-steps li::marker { color: var(--muted); font-variant-numeric: tabular-nums; }
.how .chip--warn { --c: var(--warn); }
</style>
<p class='page-sub'>What is actually running behind this window, and who does what.</p>

<section class='how-sec'>
<h2><span class='how-no'>01</span>The loop</h2>
<p>Every minute, two pulses beat against an append-only ledger on Cloud SQL:</p>
<ol class='how-steps'>
<li><strong>The clock</strong> creates jobs from your automation rules and the calendar,
hands them out, checks results, and plans visits from recurring agreements.</li>
<li><strong>The AI</strong> (Gemini, running as a worker named Nomi) arrives uncalled,
picks up a job, reads its source, and either submits a result with evidence,
asks you a question, or reports that it is stuck — with its own assessment of why.</li>
<li><strong>You</strong> — the director — do the only things a machine is never allowed to:
approve, send back, answer, abandon, and <em>sign</em>. A visit note becomes a medical
record only when a human signs it; from that moment the database itself refuses
any edit or delete.</li>
</ol>
<p>Everything is an event appended to the ledger. Nothing is overwritten,
so <a href='/activity'>Activity</a> can always answer "what happened, and who decided it."</p>
</section>

<section class='how-sec'>
<h2><span class='how-no'>02</span>Who is who</h2>
<p>The sidebar seat is a <em>declared name, not a login</em> — this demo deliberately has no
authentication. Power never comes from the name: signing and bedside services require a seat
on the clinician register, rulings and month-end confirmation require the director role on the
staff register, and approvals require owning the rule. An unknown seat can sit, and press nothing.</p>
<table class='how-who'>
<tr><td><span class='chip'>Director</span></td>
<td>The human in charge — that is you. Every judgment in the system is theirs.</td></tr>
<tr><td><span class='chip'>Nomi</span></td>
<td>The AI worker. It drafts, asks, and assesses — it cannot approve or sign anything.</td></tr>
<tr><td><span class='chip'>Clock</span></td>
<td>The pulse. It creates and checks work on schedule. It never judges either.</td></tr>
<tr><td><span class='chip'>Dr-A · Dr-B · Dr-C</span></td>
<td>Clinicians in the (fully synthetic) EMR who carry out and sign visits.</td></tr>
<tr><td><span class='chip'>Sim-Director</span></td>
<td>A scripted stand-in that presses human buttons while judging is under way,
so the demo keeps moving: it approves finished work, signs delivered drafts
(while judging runs it is placed on both registers — signed notes honestly read
"signed by Sim-Director"),
and confirms month-end claims once a month has ended and holds no flags.
It never answers questions and never rules on a flagged charge — those wait
for a person. Synthetic patients, synthetic director — and every press is
labeled with this name in Activity.</td></tr>
</table>
</section>

<section class='how-sec'>
<h2><span class='how-no'>03</span>The color grammar</h2>
<p>Only four buttons in the whole product are ever filled solid:
<strong>Sign</strong>, <strong>Approve</strong>, <strong>Reply</strong>, <strong>Confirm</strong> (a month-end claim) —
the heaviest human judgments. Everything else is quiet.
<span class='chip chip--signed'>Green</span> means signed or passed,
<span class='chip chip--warn'>amber</span> means a human is needed,
red is destructive or expired, blue is information, gray is inert.</p>
</section>

<section class='how-sec'>
<h2><span class='how-no'>04</span>What the AI cannot do — by construction, not by policy</h2>
<ul>
<li>It cannot approve its own work. No code path exists from the agent to approval.</li>
<li>It cannot sign a medical record, or touch one that is signed.</li>
<li>It reads only <em>signed</em> notes — its own unsigned drafts are never its source.</li>
<li>Its word is never evidence — a result must quote the source, or the clock sends it back.</li>
<li>It stops at its budget: calls, seconds, and retries are limits carried by every job.</li>
<li>The <a href='/guide'>guide</a> you can chat with holds no writing tools at all —
it can point at a page, and nothing else.</li>
</ul>
</section>

<section class='how-sec'>
<h2><span class='how-no'>05</span>Where it runs</h2>
<p>Cloud Scheduler fires two Cloud Run Jobs every 60 seconds; this window is a
Cloud Run service; the ledger and the synthetic EMR are Cloud SQL for PostgreSQL;
the model is Gemini via Vertex AI, reached with the workload's own identity —
no API key exists anywhere. Every patient, address and clinician is invented;
patient homes are stood in by public landmarks.</p>
</section>
</section>
"""
