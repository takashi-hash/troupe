"""説明 — この仕組みは何がどう動く？（人に見えるもの §1）

環の図・登場人物・色の語彙・**AI にできないこと**。静的——**集める操作は無い**。
"""

from __future__ import annotations


def _説明() -> str:
    # 頭は頁の決まり（style.py §2）——静的な頁なので数える物は無く、件数札は出さない
    return """
<div class='page-head'><h1 class='page-title'>How Troupe works</h1></div>
<section class='how'>
<p class='page-sub'>What is actually running behind this window, and who does what.</p>

<div class='form-card'>
<h2>The loop</h2>
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
</div>

<div class='form-card'>
<h2>Who is who</h2>
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
so the demo keeps moving. Synthetic patients, synthetic director — and every
press is labeled with this name in Activity.</td></tr>
</table>
</div>

<div class='form-card'>
<h2>The color grammar</h2>
<p>Only three buttons in the whole product are ever filled solid:
<strong>Sign</strong>, <strong>Approve</strong>, <strong>Reply</strong> —
the heaviest human judgments. Everything else is quiet.
<span class='chip chip--signed'>Green</span> means signed or passed,
<span class='chip chip--warn'>amber</span> means a human is needed,
red is destructive or expired, blue is information, gray is inert.</p>
</div>

<div class='form-card'>
<h2>What the AI cannot do — by construction, not by policy</h2>
<ul>
<li>It cannot approve its own work. No code path exists from the agent to approval.</li>
<li>It cannot sign a medical record, or touch one that is signed.</li>
<li>It reads only <em>signed</em> notes — its own unsigned drafts are never its source.</li>
<li>Its word is never evidence — a result must quote the source, or the clock sends it back.</li>
<li>It stops at its budget: calls, seconds, and retries are limits carried by every job.</li>
<li>The <a href='/guide'>guide</a> you can chat with holds no writing tools at all —
it can point at a page, and nothing else.</li>
</ul>
</div>

<div class='form-card'>
<h2>Where it runs</h2>
<p>Cloud Scheduler fires two Cloud Run Jobs every 60 seconds; this window is a
Cloud Run service; the ledger and the synthetic EMR are Cloud SQL for PostgreSQL;
the model is Gemini via Vertex AI, reached with the workload's own identity —
no API key exists anywhere. Every patient, address and clinician is invented;
patient homes are stood in by public landmarks.</p>
</div>
</section>
"""
