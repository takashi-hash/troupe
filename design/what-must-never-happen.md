# Troupe (Ichiza) — What must never happen

**Version**: v1.0 (2026-08-21)
**Role**: **The source of the whole design.** Every invariant, every aggregate boundary, every piece of type work is drawn from here.

> **This file is a translation.** The source of truth is [`設計/起きてはいけないこと.md`](../設計/起きてはいけないこと.md). The reconciliation tests read the Japanese file, not this one — where the two disagree, the Japanese is right.

Troupe is "a workplace where the AI moves the work along and **the judgment stays human**."
So there are only two kinds of thing to protect — **work must not fall on the floor**, and **judgment must remain the human's**.

---

## 1. The list

A row that cannot say **what failure looks like** is not written down. "X is incorrect" is not a way of writing failure.

| # | What must never happen | What failure looks like |
|---|---|---|
| **F1** | Work that was asked for passes its due date with nobody noticing | There is an overdue job, and not one of them appears on the Today screen |
| **F2** | Recurring work only starts when a person remembers it | A monthly rule is active and no job for that month has been created |
| **F3** | Something goes outside without a person having judged it | An outward-facing result exists and the ledger has no approver and no time of approval |
| **F4** | What happened cannot be explained | For a given job, "who · when · what · how" cannot be laid out |
| **F5** | Something is recorded as finished that is not finished | It is recorded as complete and no ground for saying so can be pointed at |
| **F6** | Warnings stop being read | The same warning appears every day and the person no longer looks at the screen |
| **F7** | The ledger breaks quietly | Old records cannot be read, no error is raised, and it keeps running |
| **F8** | The checks lie | A rule that is supposedly held is broken and the checks stay green |
| **F9** | The design and the program drift apart | What the design says exists nowhere in the code |

---

## 2. Where these came from

- **F1 · F2 · F4** came from a person's own words. "Billing ends up in the following month." "Asked for today, done tomorrow."
  "Routine work is decided by the month… the assumption is the AI creates it on its own."
  "Don't we have to be able to see who did what, when, and how?"
- **F3** comes from the axiom. **Judgment is human.**
- **F5 · F6** are the underside of F3 · F4 — pretending to have judged, and no longer looking, are both roads to losing the judgment.
- **F7 · F8 · F9** **actually happened to Troupe itself.** Nobody read the version-number table.
  Two of the checks stayed green when the thing they guarded was broken. Nineteen design documents and eighty code files drifted apart, and the whole thing went back to a blank page.

---

## 3. What this demands

| Failure | What it demands |
|---|---|
| F1 | Jobs carry a due date. Overdue jobs are gathered in one place, every day |
| F2 | Jobs are created from rules automatically. Never created twice |
| F3 | Approval survives as a record. Nothing moves on without one |
| F4 | **A change of state and the event that gives its reason are always recorded together** ← demands an aggregate boundary |
| F5 | Finishing requires evidence. With no evidence, a date to check again is required |
| F6 | Do not show anything a person can do nothing about right now |
| F7 | The ledger declares its own shape, and refuses to open if the shape does not match |
| F8 | A check is used only after it has been broken and seen to go red |
| F9 | Every line of the design has someone enforcing it |

**Only F4 demands a "boundary."** It is the only one saying: two things must be protected in a single write.
[Aggregates](what-a-job-is.md) are drawn from here.
