# Troupe (Ichiza) — What people see

**Version**: v2.0 (2026-08-22)
**Role**: The screens, and the values handed to them. **They make not one business judgment.**

> **This file is a translation.** The source of truth is [`設計/人に見えるもの.md`](../設計/人に見えるもの.md). The reconciliation tests read the Japanese file, not this one — where the two disagree, the Japanese is right.
>
> *Translator's note on names:* the design names the screens; the web window labels them slightly differently. Today = **Inbox**, Schedule = **Automations**, History = **Activity**, Route = **My Day**, Visit = the visit screen opened from a stop, How = **How Troupe works**.

---

## 1. Screens

| Screen | The question it answers | What it shows | Which failure it is for |
|---|---|---|---|
| **Today** | What needs my judgment and my eyes right now? | Only what `judge_today` returned | F1 · F6 |
| **Schedule** | What is coming? | Jobs already created (**every column but the terminal ones — shown as search rows, and a row opens the detail**), and what the rules × the calendar imply has not been created yet | F1 |
| **History** | What did we ask for in the past, and what got done? | The column of events (**each with the heading of its job** — a row opens the detail) | F4 |
| **Detail** | For this job: who · when · what · how? | Every event, and the bodies of the questions, answers and assessments | F4 |
| **Search** | Where is that job? | Pulls it up, finished ones included | F1 |
| **Patients** | Who is this person, and what is going on? | A copy from the medical record (**another bounded context**) plus **the list of agreements and put on / end** (an agreement is a fact about a patient — it does not get a page of its own). A reference for reading the chart before approving — **not translated into our words** | F4 |
| **Route** | Today, who goes where and in what order? | That day's visits per clinician, nearest-from-base first. A map and distances — **a patient's home is stood in for by a public place** (not one real residence is ever pointed at) | F1 |
| **Visit** | What do I record on this visit, right now? | Opened from a stop on the route. S/O/A/P **prefilled from the draft**, and the signature — signing marks the visit done and the draft used, and **the record becomes next week's material for the AI** | F4 |
| **Billing** | This month, who owes what, and what is snagged? | **Two faces** — the claim face (month × patient claim cards · ruling on flags · confirmation · the submission file · the invoice) and the **fee-schedule face** (a copy of the master). **Both the points and the payer are entirely fictional** | F1 |
| **Guide** | What should I do, and where? | The text of an answer to a question, and **whitelisted links to screens only** (an invitation to anywhere outside stays plain text). The LLM composes the answer — **the person does the pressing**. Nothing is written to the ledger | F6 |
| **How** | What is this thing and how does it work? | The diagram of the loop · the cast · the colour vocabulary · **what the AI cannot do**. Static — **there is no gathering operation** | F6 |

**Only "Today" pushes.** The rest are drawers you pull open. That split is what prevents F6 (stops being read).

---

## 2. The values handed to the screens

**Only text and IDs reach a screen.** No aggregate and no value object goes out.
**Today's material** (the domain values the specification looks at) and **today's row** (the text the screen looks at) are different things — `gather_today` repacks material → specification → row, in that order.
**The repacking belongs to app** — if a screen repacked for itself, the screen would know the shape of the centre.

| Value | What is in it |
|---|---|
| Today's row (**the canonical one**) | Job id · `RuleName` and the version number it was born from · **the period** (for a requested job, the head of the request body) · **the instruction** (copied at birth — **without the original text there is no way to approve**) · the state's name · due date · the assignee's name · recheck date · **the body of the result** · **the quote that is the evidence** · **the body of the question** · **the body of the answer** · **the body of the assessment and its reason** · **whether retries are exhausted** · **the amount spent and the budget** · the owner · **what can be pressed** |
| └ The bodies go in as they are. **They are not shortened, and not only on the pushing screen.** **The owner is the same person as the viewer** (§3), so the screen does not show it |
| Event row | Time · **who** (the name; failing that **the word for the actor** — there is one bridge) · what happened |
| Schedule row | Rule name · instruction · version number · the active version · the next period · what can be pressed |
| Detail | Job id · **instruction** · the state's name · due date · assignee · **the body of the result** · the quote that is the evidence · recheck date · **the whole column of question-and-answer pairs** (Today shows only the latest pair; Detail shows all) · **the body of the assessment and its reason** · what can be pressed · the column of events |
| History row | Time · who (**kind and name** — the kind is what tells human, AI and clock apart on screen) · what happened · **the job id and its heading** (rule and period; failing that, the head of the instruction). **The column can be pulled newest-first in slices** — it never carries everything at once |
| Search row | Job id · heading · period · instruction · the state's name · due date · the assignee's name |
| Filter conditions | Keyword · the state as displayed · rule · assignee (**text only**) |
| Patient row | Patient code · age · living situation · principal diagnosis · next visit · physician-order expiry (**in the other context's words, untranslated**) |
| Route row | Order · **visit id** · patient code · the name of the place (the public stand-in) · the purpose of the plan · **distance from the previous point** · coordinates (only so the map can be drawn) · **how the draft stands** (signed / draft present / none) · **state** (planned / done / cancelled — **a finished visit stays in today's line-up**; a route that hides progress is useless in the field) |
| Agreement row | Id · patient code · weekday · **interval in weeks** · clinician · purpose · start · end |
| Visit detail | Visit id · date · the patient summary (every field of the patient row) · **the unused draft** (body and id) · **the column of signed records** · **the column of services** · the roster of clinicians |
| Patient detail | Every field of the patient row, plus the column of **prescriptions currently running** · the column of status changes · the column of **drafts (proposals Troupe left; before signing)** · the column of **signed records** (date · clinician · S · O · A · P). **Nothing can be pressed** — it is a read-only copy. **Drafts and signed records are separate fields** — a proposal and a fact are never mixed into one column |
| Fee-schedule row | Code · name · kind (visit / urgent / service / drug / material / add-on / monthly) · points or yen · the unit it is claimed by · cap · note |
| Charge row | Id · patient · date · **visit id** (a monthly row has none) · code · name · quantity · points · state (derived / flagged / ruled through / struck) · the reason for the flag · the reason for the ruling |
| Claim copy | Patient · month · state (draft / confirmed) · total points · the co-payment ratio · the amount owed · the column of charge rows · who confirmed it and when |
| Seat-and-role row | The seat's name · the role (director / clinician) |
| Guide answer | The text of the question · the text of the answer · the recent exchanges (**the screen carries them around — they are not put in the ledger**) |

**They have no behaviour.** They are containers, nothing more.

### Questions, answers and assessments arrive as they are — this is where the worth of the whole thing reaches the person

| Field | Enforced by | How to break it |
|---|---|---|
| The body of the question | The repacking in `gather_today` (it goes in as it is) + the week-A run-through | Red if summarising or truncating creeps in |
| The body of the answer | Same | Same |
| The body of the assessment and the reason it was read that way | Same, plus the obligation on `Assessment` (it cannot be constructed with an empty reason) | Red if an assessment with an empty reason reaches the screen |

**Do not shorten** — shortening leaves less to judge with. Without the assessment, all that reaches the director is the number "spent all twenty calls."

---

## 3. What can be pressed

**The domain specification composes it** ("which operations may a person press on this job right now").
app asks, and puts what comes back into the value. **The screen only shows what is in there.**

| Operation | Where it appears | Who sees it |
|---|---|---|
| Approve | Today · Detail | **The owner only** |
| Send back | Today · Detail | The owner only |
| Answer | Today · Detail | Only the person who was asked (= the owner) |
| Abandon | Today · Detail | The owner only |
| **Add a version** · **Activate** · **Deactivate** | Schedule | Any person (the version fields are **prefilled from the topic's data, and the person overwrites them**). **Deactivate only while an active version exists** — the specification composes that. **None of these appear on Today** |
| **Agree a recurring visit** · **End one** | Patients | Any staff member (arranging with a patient happens to clinicians and to office staff alike). **Ending one drops the future visits it produced to cancelled** |
| **Add a service** · **Remove one** | Visit | **A clinician's seat only** (the clinicians register is the gate). **Only before signing** — signing freezes it |
| **Rule on a flagged row** · **Confirm the monthly claim** | Billing | **The director's seat only** (the role in the staff register is the gate). Confirmation only **after the month has ended** — once confirmed it cannot be rewritten |
| **Sign and end the visit** | Visit | **A clinician's seat only.** **The signer is the seat that pressed it.** **Signing applies only to a visit still planned** — done and cancelled are refused |
| **Skip this visit once** | Visit | Any staff member (cancelling a plan is office work too) |
| **Request** | Schedule | Any person (a one-off job). **All a person must write is the request body, the source and the required terms** — the rest is defaulted (canonical in [how work moves §1](how-work-moves.md)). From the moment it is requested it **appears in the column of scheduled jobs**, and reaches Today only when it needs judgment |

**The worst thing is pressing something and nothing happening.** When it is refused, the reason comes back as a **refusal** (`Refusal`) — not your job to approve, someone already approved it. **A refused operation is not an error** — the job's state does not change, so its life is unscarred and the reason appears on the screen only.

---

## 4. What goes on Today

**`judge_today` decides. This screen only lines them up.**

| What is shown | What the person can press now |
|---|---|
| Waiting for approval | Approve · Send back |
| Waiting for an answer | Answer |
| **An assessment has been written** (only while in progress or failed) | Send back · Abandon (**reading alone is not something to press**) |
| Past its due date, with an operation a person can press | That operation |
| A self-declared finish whose recheck date has come | Send back |
| Retries exhausted and still standing | Send back · Abandon |

**Every row carries at least one thing the person can press right now.** A row without one is not shown.

### What is not shown

| Not shown | Why |
|---|---|
| A job the AI has in progress with **no assessment written** | There is nothing the person can do right now (with an assessment, it appears) |
| A failure in the middle of retrying automatically | Same |
| A job before its due date with **no** operation a person can press | Future plans do not go on Today (the red gets buried). **With an operation to press it appears even before the due date** |
| Finished jobs · abandoned jobs | They are done |

**If the same thing shows up day after day, the design has failed** (F6) — suspect that there is no real operation to press.

---

## 5. Rules

- **What appears on screen is the glossary word itself.** No screen rephrases it.
  If it reads badly, **rename it in the glossary**.
  When showing it to someone who does not read Japanese, **the glossary identifier may be shown alongside** —
  not by inventing a translation, but by showing the bridge in the [glossary](what-a-job-is.md) as it is. **The bridge stays the single file `words`**
- **A list read does not reconstruct the aggregate.** A Reader pulls it in the shape the screen needs.
  **A read with no boundary to protect has no need of the aggregate's shape**
- **Screens do not import domain**
- **If it can be counted, say the count first.** The head of a page is "heading · count · next move" — the first screenful reads as "how many there are, and what to do next." Scrolling is for detail only (the canonical look lives at the top of `ui/web/style.py`)
