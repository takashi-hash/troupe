# Troupe (Ichiza) — How we build it

**Version**: v2.0 (2026-08-22)
**Role**: The format of the design documents, the layers, the folders, and the devices that go red. **Read this one first.**

> **This file is a translation.** The source of truth is [`設計/どう作るか.md`](../設計/どう作るか.md). The reconciliation tests read the Japanese files, not these — where the two disagree, the Japanese is right. **Do not design from this folder**; add to `設計/` and translate afterwards.

---

## 0. Why it was folded up again

Fourteen sheets became five. **One concept scattered over six sheets was the reason none of the four run-throughs got through** —
the rule "fill in six places at once" was treating a symptom (**while it is scattered, something always gets left out**). So **we stopped splitting by structural element and split by "what it carries / how it moves / what people see."**

---

## 1. Last time's failures (all confirmed on the real thing)

| # | Failure | What prevents it |
|---|---|---|
| 1 | Classified, with no obligation attached (0 checks) | Rule 2 |
| 2 | Only states were forbidden; values, 0 | Rule 2 |
| 3 | The devices that go red were all "names and where things live." **Not one looked at whether the types guarantee correctness** | Rules 1 · 7 |
| 4 | **Procedure and mutual exclusion** were put in the core | Rule 5 |
| 5 | Six aggregates, and **zero** invariants that demanded a boundary | Rule 5 |
| 6 | **451 of 1539 lines** at the centre were something other than rules. Optimistic locking was exposed in an interface | Rule 6 |
| 7 | Words were invented (299 of them. "The place tasks are put") | Rule 4 |
| 8 | Five places counted things, and no two agreed | Rule 3 |
| 9 | Declarations with nobody to carry them out (4 kinds with zero appenders) | Rule 1 |
| 10 | The devices lied (two stayed green when broken) | Rule 7 |
| 11 | **The AI was placed outside and generic** — leaving nowhere to put its operations | Rule 5 |
| 12 | **One concept scattered over six sheets** — none of the four run-throughs got through | **This refolding** |

---

## 2. Rules of format

### Rule 1 — one line carries the claim, the enforcer, and how to break it
**The enforcer column cannot be left blank.** If there is none, write "nobody yet."
**If you cannot write how to break it, do not force one** — write that you cannot (a "how to break it" written to fill a column has turned a correct implementation red).

### Rule 2 — a classification comes with an obligation
If you write "this is a value," put **a sentence that reads as a test** beside it. A row with an empty obligation has not classified anything.

### Rule 3 — anything counted has one canonical home
Do not put counts in headings. Do not copy another document's count. Refer to it.

### Rule 4 — words are business words only
Pattern names (value object, aggregate, domain service, factory, repository, application service, presentation) are used **in their standard Japanese form** and **are not listed in the glossary**.
Translating a role word into Japanese makes us build code names out of it.

### Rule 5 — the core and the aggregates are drawn from what must be protected
The core is **only what needs a business judgment**. Procedure and technology do not go in.
An aggregate is built only from an invariant that could say "**a boundary is required**."

### Rule 6 — a layer's "what must not be put here" is written first
"No business rules here" is written for every layer except the centre.

### Rule 7 — a device is finished only when "broken and seen to go red" is written down
What has not been confirmed is not written as "placed." **The ritual itself can lie.**

### Rule 8 — no citing of sources
### Rule 9 — design files have Japanese names, are all .md, and sit directly under `設計/`

---

## 3. Five documents

| Document | What it decides |
|---|---|
| [What must never happen](what-must-never-happen.md) | **The source of the whole design.** What must be protected |
| [What a job is](what-a-job-is.md) | The domain, the core, words, values, aggregates, invariants, states and transitions, killing it with types |
| [How work moves](how-work-moves.md) | Who starts things, where the judgment sits, factories, interfaces, events |
| [What people see](what-people-see.md) | Screens, the values handed to them, what can be pressed, what goes on Today |
| How we build it (this one) | Format, layers, folders, the devices that go red |

**When you add something, it must close inside that one sheet.** If it does not close, the split is wrong.

---

## 4. Layers

**Dependencies point inward only.** That is the whole of the onion's claim.

| Layer | **What must not be put here** | What goes here |
|---|---|---|
| **domain** (the centre) | **Clock, randomness, storage, screens, outside tools.** "Now" arrives as an argument | Value objects, entities, aggregates, invariants, domain services, specifications, factories, the names of events, the declarations of Repository and Store |
| **app** | **Business rules** | Application services (canonical count in [how work moves §1](how-work-moves.md)), transaction boundaries, repacking into DTOs, the declarations of Port and Reader |
| **adapters** | **Business rules** | The ledger's implementation, the implementations of Ports, **the anti-corruption layer (ACL)** |
| **ui** | **Business rules** | Screen widgets. **It does not know domain** — presentation (the bridging) is app's entrance (**it receives text and assembles values**) and the DTOs |

### The context

There is one, for now. Its name is Troupe. **The AI as a worker is inside it.**

Outside are — **the topic** (poured in), **the source** (translated by the anti-corruption layer),
**the LLM tool** (translated by the anti-corruption layer), the ledger, the clock, the screens.

**An anti-corruption layer (ACL) sits on both the source and the LLM.** Both speak outside words and are translated into ours before entering —
the LLM's response into a marked `Reply` (**the routing is a domain specification**), the source's contents into material, quote and the reason it could not be read.

### Locking

| Thing | Where | Why |
|---|---|---|
| Optimistic locking | **Hidden inside adapters** | It is not a business word |
| Who the assignee is | domain | It is a business word |
| Dropping an assignee on timeout | app | It is a mutual-exclusion device |

---

## 5. Folders

| Path | What lives there |
|---|---|
| `main.py` | The root of assembly. Belongs to no layer. **The only place concretes are poured in** |
| `domain/obligations.py` | The obligations common to everything. **The only file that holds no concept** |
| `domain/value_objects/` | Value objects — people · calendar · rule · job. **One value, one file** |
| `domain/aggregates/` | Aggregates — job (root `job`, life `life`, **one operation one file**) and rule |
| `domain/events/` | Domain events — job · rule. One event, one file. **Operations stamp them** |
| `domain/services/` | Domain services and specifications — checking, routing, reconcile |
| `domain/repositories/` | The declarations of repositories — Repository and Store, one declaration one file. **The write gate (I1)** |
| `app/ports/` | The **declarations** of Ports and Readers — one declaration one file. **The only pour-in points** |
| `app/services/` | Application services — one operation one file in **the folder of whoever raises it** (human · agent · clock · screen) plus `refusal` (**the refusal** — the return of every operation). **Only human carries judgment** (canonical count in [how work moves §1](how-work-moves.md)) |
| `app/dto/` | **DTOs** — outbound and inbound (the canonical field lists are in [what people see §2](what-people-see.md) — no counts here). **Text and IDs only** |
| `adapters/` | Implementations — the ledger, topics, the clock, id assignment, **the medical record's ports (`emr`) — the beat (automatic) may write exactly three things: into the drafts inbox (**addressed to a visit — once per (patient, visit date)**), agreement-derived visits, and charges derived from signed visits (there is no port to rule on a flag or confirm a claim). Only human operations can write agreements, the end of a visit (appending a signed record, skipping this one), recording services before signing, ruling on flags, and confirming the monthly claim (**the beat's ports have no ruling and no confirming**). **The role gates are on the medical record's side too** — signing and recording services only from a seat present in clinicians; ruling and confirming only from a seat whose role in staff is director (a seat is a claim of name; authority comes from the register). **The two registers are separate concerns** (the signing roster and the register of roles) — dropping clinicians.active leaves the clerical gate open as long as the staff entry stands. **Audit columns with no reader** (the cancellation reason, who recorded, who ruled) are held under the declaration "written but not shown". There is nowhere a port that rewrites an appended signed record, and nowhere a port that creates a patient.** **The ledger has two implementations, local (SQLite) and cloud (Cloud SQL), behind one port.** **The anti-corruption layer (ACL) is isolated in `acl/`** — only the two sheets that translate outside words (llm · source) live there (llm holds Ollama and Gemini). The rest are plain ports |
| `ui/` | **Screens** — one screen one file (today · schedule · history · detail · search. **Patients (agreements included) · route · bedside entry · billing (the fee-schedule face included) · guide · now (the explanations live dissolved into its parts; the raw feed = SSE is also the shell's port — the same read repeated) live only in the web shell** — the desktop window does not have them) plus **the shells** (`shell` = the desktop window, `web` = the web window — **web is a folder; apart from routes and the frame it is one screen per file**. Neither holds a beat) plus `words` (the bridge for operation words — **one canonical home**). **It shows what it was given, and when pressed calls app with text** |
| `launchd/` · `cloud/` | **The wiring for residency** — raising the clock's round and the AI's round on a period (launchd locally, Cloud Run Jobs and Scheduler in the cloud). **Configuration of bought mechanisms, not code** ("wake the AI" never appears in the clock's table). **If the patients are synthetic, so is the director** — for the duration of judging, a scripted stand-in (Sim-Director) may press the human operations. **It is stated on the screens and in the README** |
| `tests/` | The devices that go red |
| `design/` | **The English translation of these five sheets** (for readers outside). **The canonical home is `設計/`** — the reconciliation tests read the Japanese only. Where they disagree, the Japanese is right. **Do not design from here** |
| `custom/<topic>/` | The data for a topic (`Topic`). **Never code** (the runtime ledger is `data/` — not committed) |

**The grouping takes the pattern name; the file is a business concept** (a human judgment) — one concept, one file, in values · aggregates · events · services. For approval: the value `Approval`, the operation `approve`, the event `Approved`, one sheet each on its own shelf.
**An operation's argument type is the "from," its return type is the "to," and the return is always the pair (next shape, event)** — I1 and the transition table become types, and the reconciliation test matches the design's table against the signatures line by line.
**The aggregate is the boundary** — the one-way `job → rule → calendar · people → obligations` is held by the dependency contracts. **Rules do not know about jobs.**

**Do not create a file that is not in this table** — `utils`, `helpers`, `common` are born where this gets loose. **File names are design words** — `ls domain/` should read as what exists in the business.

---

## 6. The devices that go red

**If the kinds are lopsided, it is unfinished.** Last time all seven were "names and where things live,"
and not one looked at whether the types guarantee correctness.

| Kind | What it protects |
|---|---|
| **Types** | An invalid value or an invalid state **cannot be written** |
| **Automated tests** | The example is the specification. Given this material, this happens |
| **Reconciliation** | Whether the design's tables and the real thing agree |
| **People** | Only what can be written down to who reads it and when |

**Anything without "broken it and saw red" written down is not called placed.**

When implementation starts, **place them in this order** — the obligations on values, forbidden values, forbidden states, first.
Last time these were never placed at all.

---

## 7. When to stop designing and start writing code

**Stop trying to finish the design before building.** The previous Troupe got to 19 sheets and 80 files and was thrown away **without ever running one real week through it**. This time too, five run-throughs and 0 lines.
**We are trying to decide in the design things that cannot be known without running.**

### Split the stalls in two

The stalls a run-through finds are of two natures. **Only one of them gets closed.**

| Kind | What it is | What to do |
|---|---|---|
| **Needs design** | It contradicts / the material exists nowhere / there is nowhere to put it / it is circular | **Close it** |
| **Decided in implementation** | Concrete values, the fine detail of ordering, wording, which type to represent it with | **Do not close it. Write "decided in implementation" and leave it** |

**Closing all of them is impossible** — read adversarially, they are endless.
**Close only what must be closed.**

### The point of convergence

When these three hold, stop designing and start writing code.

| Condition | How it is measured |
|---|---|
| **A week that goes well runs through to the end** | The run-through of "trace week A" reaches the end with 0 stalls |
| **The remaining stalls are all "decided in implementation"** | Zero stalls classified as "needs design" |
| **The design has not passed five sheets and 1100 lines** | Past that, add nothing. To add, delete something |

**The week that falls over (week B) does not have to run through.** Trying to make the failing week run through in the design means deciding things that have not even happened.
**Run it, actually fall over, then fix it** — a scenario actually made to fall over is then held by a fixed test.

### The rules once writing has started

| Rule | Why |
|---|---|
| **The design does not pass five sheets and 1100 lines** (raised from 1000 for the second bounded context, the medical record. The rule against adding without a reason still stands) | It scattered at 2000 lines. Without a cap it always swells |
| **The devices that go red are placed together with the code** | Leaving them all as "nobody yet" during the design stage means they never get placed (which is what happened last time) |
| **Once week A runs through, the next thing is code, not week B** | Something that runs, first. The failing week comes after it runs |
| **What running it taught you goes back into the design** | Without that, design and code drift apart again |

---

## 8. What to confirm when you finish writing

1. Is any enforcer column empty?
2. Does every classification row have an obligation written?
3. Is any count written in two or more places?
4. Has a non-business word got into the glossary?
5. **Does it contradict an earlier document?** — if it does, **go back**. Do not paper over it in the current document
6. Have you broken it and seen it go red?
7. **Does it close inside this one sheet?** — if not, suspect the split

**5 and 7 matter most.** Last time, every contradiction got a "but" appended to paper it over,
and that accumulation made "the design is right, the implementation just does not match."
