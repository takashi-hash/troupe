# Troupe (Ichiza) — What a job is

**Version**: v2.0 (2026-08-22. Fourteen documents folded into five. **One concept scattered over six sheets was the reason four run-throughs all failed** — every addition left a hole somewhere, so "what a job carries" is closed inside this one sheet.)

**Role**: The word *job*, what is inside it, what must be protected, and the shapes it may take. **It closes here.**

> **This file is a translation.** The source of truth is [`設計/仕事とは何か.md`](../設計/仕事とは何か.md). The reconciliation tests read the Japanese file — the value-object list in §3, the transition table in §6 and the glossary in §2 are parsed straight out of it — not out of this one. Where the two disagree, the Japanese is right.

---

## 1. The domain and the core

**Keep the work moving without dropping it, and leave the judgment with the person.**

| Class | Area | How it is treated |
|---|---|---|
| **Core** | The life of a job / a person's approval and send-back / the ground for saying it is finished / rule versions and activation / **the path by which the AI does one job** | Built with care |
| **Supporting** | The content of the rules per topic / how screens look | Thin. **Poured in as data** |
| **Generic** | Storage / the mechanism that runs on a cycle / **the mechanism that keeps the AI resident** / mutual exclusion / **the tool that calls an LLM** / screen widgets | Bought |

### The axiom — judgment is human

The AI creates, does, checks and lines up. **It does not decide.**
Approve, send back, answer, activate, deactivate, abandon — those six can be raised only by a person (**I7**).

**There are two roads from the AI to the person.** A question (not enough material) and an assessment (what it read, and a proposal).
Neither is a judgment. **Without the assessment the AI can only give a number** —
not "spent all twenty calls" but "all twenty fell over for the same reason; the source has most likely moved."
That is the worth of this thing.

### The AI splits in two

| | Which side |
|---|---|
| **The tool that calls an LLM** (model, API) | **Outside · generic.** Bought |
| **The AI as a worker** (holds an assignment; takes work, asks, submits, falls over, writes assessments) | **Inside · core** |

Without the split, the second one ends up outside. It actually did, and then there was nowhere to put the AI's operations.

---

## 2. Words (**the Japanese ⇄ identifier bridge lives only here**)

**Only business words go in here.** Pattern names (value object, aggregate, repository…) are used in their standard Japanese form and **are not listed in the glossary**.

### People and places

| Word | One-line definition | Identifier |
|---|---|---|
| 人 · person | The one who judges | `Human` |
| AI | The worker that does jobs. Holds an assignment. **Does not judge** | `Agent` |
| 帳簿 · ledger | Where what happened and how things stand are kept. **Never rewritten, never deleted** | `Ledger` |

### The job

| Word | One-line definition | Identifier |
|---|---|---|
| 仕事 · job | One item, from being asked for to being finished | `Job` |
| 仕事の識別子 · job id | Unique. Never changed afterwards | `JobId` |
| 作成元 · origin | Where it was born from. **The key that prevents creating it twice** | `Origin` |
| 依頼 · request | The fact that a person said "do this" | `Request` |
| 期日 · due date | The time by which it should be finished | `DueDate` |
| 確かめ期日 · recheck date | When it finished with no evidence, the time to check again later | `RecheckDate` |
| 担当 · assignee | Whoever holds it now. A person or an AI | `Assignee` |
| 起こす者 · actor | Whoever raised that hand. Human, AI or clock. **Distinct from the assignee** (a screen raises nothing — the person who opened it is the actor) | `Actor` |
| 受け持ちの人 · owner | The person who approves and receives the AI's questions. **The version decides it** | `Owner` |
| 成果 · result | What the job produced. Never rewritten once submitted | `Result` |
| 根拠 · evidence | The backing for saying it is finished. **A quote read from the source.** The AI's own words are not evidence | `Evidence` |
| 承認 · approval | The fact that a person decided "this may proceed" | `Approval` |
| 差し戻し · send-back | The fact that a person decided "not yet" | `SendBack` |
| 質問 · question | What the AI asks when it lacks material. **It does not ask for a judgment** | `Question` |
| 回答 · answer | The fact that a person answered | `Answer` |
| 見立て · assessment | What the AI read of the situation, and why. **Not a judgment** | `Assessment` |
| 使用上限 · budget | How many calls and how much time may be used. **The safety valve that stops a runaway** | `Budget` |
| 使った量 · spent | Calls and seconds used so far | `Spent` |
| 整えた応答 · reply | The LLM's response after the anti-corruption layer has shaped it. **A mark** and a body | `Reply` |

### The rules

| Word | One-line definition | Identifier |
|---|---|---|
| 業務ルール · rule | The rule for recurring work. This is what gives birth to jobs | `Rule` |
| 業務ルールの識別子 · rule name | Unique | `RuleName` |
| 版 · version | One shape of a rule. **Only ever appended** | `Version` |
| **やること · instruction** | What is to be done in that job. **The instruction the AI reads** | `Instruction` |
| 受け入れ基準 · acceptance criteria | What counts as a result. **The required terms** (the machine looks at these — **chosen from words that appear literally in the source**; the comparison is literal) and the explanatory sentence (people and the AI read it) | `AcceptanceCriteria` |
| 周期 · cycle | Monthly or weekly | `Cycle` |
| 対象期間 · period | The period that job covers | `Period` |
| 源 · source | Where the material lives. Where the AI goes to read | `Source` |
| 有効 · active | A person's judgment that this version may now give birth to jobs | `Active` |
| 検査 · check | Machine-checking whether a result meets the acceptance criteria. **It has the power to stop** | `Check` |
| LLM に問う · consult | Read the source, hand it to the LLM, receive the response. **The specification decides where it goes** | `consult` |
| やり直しの上限 · max retries | How many times it may be retried. The version decides | `MaxRetries` |

### Words we do not use

| Not used | Instead | Why |
|---|---|---|
| Task | Job | People say "job" |
| Definition | Rule | It is a design word, not a business word |
| Proof | Evidence | Same |
| Store, port, ring, procedure, assembly | **Use the pattern name as it is** | Translating a role word into Japanese makes us build code names out of it |

**One word, one identifier.** No word is given two identifiers, and no identifier two words. **The same holds for field names** — body `body`, who `by`, when `at`, start `start`, baseline `after`, name `name`, key `key`, reason `reason`, quote `quote`, recipient `to`, the text of an id `text`, days until due `days`.

---

## 3. Value objects

**Do not let an invalid value exist.** The classification is a name tag; **the obligation is the substance.**

### Obligations common to all of them

| Common obligation | How to break it |
|---|---|
| Validation runs at construction | Red if it can be built with invalid contents |
| **Equal contents means equal**. Usable as the same dictionary key | Red if two with the same contents are not equal |
| **Cannot be rewritten after construction** | Red if assignment to an attribute succeeds |

### The list

| Value object | Obligation | How to break it |
|---|---|---|
| `JobId` | Not empty. No surrounding whitespace. Never changed afterwards | Red if `JobId("")` succeeds |
| `RuleName` | Not empty | Red if `RuleName("")` succeeds |
| `Human` | The name is not empty | Red if it can be built empty |
| `Agent` | The name is not empty | Red if it can be built empty |
| `Owner` | **A `Human`, exactly.** An AI cannot be an owner | Red if it can be built from an `Agent` |
| `Assignee` | **Either a `Human` or an `Agent`.** There is no third | Red if it can be built from a bare string |
| `DueDate` | Carries a time. **Takes the start time and compares against it** (for a requested job the time of the request; for a rule-born job the time it was created) | Red if it can be built earlier than the start |
| `RecheckDate` | Carries a time. **Later than the due date.** **The previous recheck date (or the due date) + the copied cycle** — the AI does not decide it. Moves forward every time it is pushed | Red if it can be built earlier than the due date / red if pushing it does not move it forward |
| `Budget` | Both calls and seconds are **1 or more** | Red if `Budget(calls=0)` succeeds |
| `Spent` | Both calls and seconds are **0 or more**. A separate value from the budget | Red if it can be built negative |
| `Period` | Only the form `2026-08` for a month, `2026-W34` for a week. **The year of a week is ISO** — a day at the start of a year can belong to the previous year's week | Red if `Period("next month")` succeeds |
| `Cycle` | Monthly or weekly | Red if a third value succeeds |
| `Instruction` | **Not empty.** A sentence from which the AI can tell what to do | Red if it can be built empty |
| `AcceptanceCriteria` | **Splits in two.** ① the column of **required terms** (not empty; **the machine looks at it**) ② the explanatory sentence (**people and the AI read it**). ① may contain `{対象期間}` — **it is opened out with `Period` at copy time**, so by the time it reaches the check it is a fixed string | Red if it can be built with ① empty / red if an unopened `{` reaches the check |
| `Source` | The location is not empty | Red if it can be built empty |
| `Origin` | For a requested job, the request's id; for a rule-born job, `RuleName` + version number + `Period` (**a version that expands per patient adds the patient code too**). **Same contents, same key string** | Red if it can be built empty / red if the same contents yield different keys |
| `Request` | Carries who asked, when, and the body | Red if it can be built with any of them missing |
| `Result` | **The body is not empty.** Cannot be swapped out once submitted. **Carries no location** — the Store that appended it returns that, and the job holds it | Red if it can be built with an empty body / red if it has a location field |
| `Evidence` | **The quote read from the source is not empty.** Carries **which source it was read from** (not where it was appended). **It is not clipped** — the moment you select, a judgment called selection enters. Folding it is the screen's presentation job | Red if evidence with an empty quote can be built |
| `Approval` | Carries **who** and **when**, both | Red if it can be built with either empty |
| `SendBack` | The reason is not empty | Red if it can be built without a reason |
| `Question` | The body asked is not empty. **The recipient is the job's owner** — the AI does not choose | Red if it can be built with an empty body |
| `Reply` | The body is not empty. **The mark is one of three: result, question, neither.** **The LLM declares the mark** (adapters only carry it). **The mark is self-declared — the specification examines it** | Red if a response with no mark reaches the specification |
| `Actor` | **One of three: human, AI, clock.** Cannot be built from a bare string | Red if a fourth can be built / red if it can be built from a bare string |
| `Clock` | The clock — it can be an actor but **never an assignee**. It has no contents | Red if it can be given a name (there is one clock; it is not told apart by name) |
| `Answer` | Carries who answered and the body | Red if it can be built with either missing |
| `Assessment` | Carries both what was read and **why it was read that way** | Red if it can be built without a reason |
| `Version` | The number is 1 or more. Always carries **instruction, acceptance criteria, cycle, days until due, budget, owner, source and max retries** | Red if it can be built with any of them missing |
| `Copied` | The bundle that gets copied — the common holdings plus days until due (canonical in §4). **The version itself is never handed over** | Red if it can be built with any of them missing |
| `TodayMaterial` | Today's material — **the domain values the specification looks at** (the canonical field list is in [what people see §2](what-people-see.md)) | **Red if it carries a "what can be pressed" field** — material and row are different things |

**That the version carries the instruction is the crux.** Without it, **the AI can never know what to do**
(found on the fourth run-through. A hole in the core).

---

## 4. Entities and aggregates

### There are two entities

| | Identity |
|---|---|
| Job `Job` | `JobId` |
| Rule `Rule` | `RuleName` |

### What a job carries (**in every state**)

**Writing it per state grows material at the next transition.** What is common is written here once.

| Holding | Where it comes from |
|---|---|
| `Origin` | Whoever raised it decides |
| The version it was born from (`RuleName` + version number) | Fixed at creation. Not rewritten when later versions are appended |
| `Instruction` · `AcceptanceCriteria` · `Owner` · `Budget` · `Source` · `Cycle` · `MaxRetries` | **Copied from that fixed version** (never taken from the current one). At copy time, `{対象期間}` in `AcceptanceCriteria` is opened out with `Period` |
| The number of retries | Born at 0. **Carried in every state.** `Retried` adds 1. **`SentBack` resets it to 0** (it does not add 1) |
| `DueDate` | The start time + the version's days |
| `Spent` | Born as `Spent(0, 0)`. **`SentBack` resets it to `Spent(0, 0)`** (from any state) |
| The location of the result, the location of the evidence | Held once submitted (empty until then). **Not written per state** — writing it per state drops it at the next transition |
| `Period` | Only for rule-born jobs |

**It copies; it does not point** — pointing would touch two aggregates in a single write.

### What a rule carries

| Holding | Rule |
|---|---|
| `RuleName` | Identity |
| The column of versions | **Only appended.** Cannot shrink, cannot be rewritten |
| The active version number | **Zero or one.** Activating version 2 automatically deactivates version 1 |
| Who activated it and when | Only a person can activate (I7) |

### There are two aggregates

**Built only from an invariant that could say "a boundary is required."**

| Aggregate | Key | The invariant that demanded it | What is protected in a single write |
|---|---|---|---|
| **Job** `Job` | `JobId` | **I1** | The change of shape, and the domain event that gives its reason |
| **Rule** `Rule` | `RuleName` | **I2** | The appended version, and the domain event that recorded the appending |

**Not made aggregates**: people, the AI (values suffice) / results, evidence, questions and answers, assessments (append-only columns, **pointed at by location**) / events (appended inside the aggregate).
**Being core and being an aggregate are different things** — the AI is core, and is not an aggregate.

---

## 5. Invariants (**canonical**)

"A boundary is required" means **two or more things break unless they are protected in one write.**

| # | Invariant | Boundary | Where it is held | Immediate / eventual | Enforced by | How to break it |
|---|---|---|---|---|---|---|
| **I1** | When the state changes, the domain event giving the reason is always left with it | **Required** | The write gate | Immediate | The ledger's gate (`save` accepts nothing but the pair) + the return type of the operations | Write a state with no event |
| **I2** | Versions are only appended. The addition and its event are left together | **Required** | The write gate | Immediate | The reconciliation in `SqliteRules` | Delete one version and write |
| **I3** | A job is never created twice from the same origin | Not required | The ledger's unique key | Immediate | The ledger's unique key (origin) | Create twice with the same key |
| **I4** | Nothing proceeds without approval | Not required | The type (Cleared always carries an `Approval`) | Immediate | The type (Cleared always carries an `Approval`) | Build it without an approval |
| **I5** | To say it is finished requires either evidence or a recheck date | Not required | The type (there are only two kinds of ending) | Immediate | The type (only two kinds of ending) | Build it with neither |
| **I6** | Only **the owner** may approve | Not required | The approve operation | Immediate | The examination in `approve` + the assignee's type in AwaitingApproval | Approve as a different person |
| **I7** | **The six human-only operations cannot be called by the AI** (approve, send back, answer, activate, deactivate, abandon). **The enforcer of the axiom** | Not required | Each of the six operations | Immediate | The type of `by` is `Human` + the reconciliation test | Call approve from the AI |
| **I8** | If a rule is active, a job for that period always exists | Not required | The reconciliation that runs on the cycle | **Eventual** | The clock's `create` + `audit` (a reconciliation on the cycle) | Stop the reconciliation and wait one cycle |
| **I9** | Among overdue jobs, **those with an operation a person can press right now** always appear on Today | Not required | The Today decision | **Eventual** | `judge_today` and its tests | Delete the overdue row from the decision |
| **I10** | The ledger declares its own shape and refuses to open if it does not match | Not required | The check when opening | Immediate | The shape number in `open_ledger` | Change the number and open |
| **I11** | A check is used only **after being broken and seen to go red** | Not required | Human hands | **Measured** | A person (the day it was put in) | — |
| **I12** | The due date is **later than the start time** | Not required | The operation that creates a job | Immediate | The type `DueDate` | Build it earlier than the start |
| **I13** | The AI may **change the shape** only of jobs it is assigned to (**taking is different** — before taking it is not the assignee. **Writing an assessment is different too** — fallen and finished jobs are exactly where an assessment is needed) | Not required | The shape-changing operations after taking | Immediate | **The examination in `consult` and `release` (the name given = the assignee)** | Change the shape of a job assigned to someone else |
| **I14** | The amount spent **never exceeds the budget** | Not required | The operation that adds to the amount spent | Immediate | `spend` and the tests for `Spent.within` | Add past the budget |
| **I15** | **A job that hit its budget, or exhausted its retries, always has an assessment** | Not required | **The AI's patrol** | **Eventual** | The patrol + the specification for whether an assessment should be written | Leave an exhausted job for one cycle and find zero assessments |
| **I16** | **The raw response never enters the ledger** — the anti-corruption layer shapes it into a `Reply` (**carrying the mark is part of the shape**) and it enters as **exactly one of** result, question or assessment. **Which one it becomes is decided by a domain specification — the LLM's declaration is not taken at face value** | Not required | The anti-corruption layer + the specification | Immediate | The type of `LlmPort` + the examination of the mark | Make the raw response the result as it is |

**Having the immediate ones does not make the eventual ones unnecessary.** Types protect the paths through the code; the eventual ones protect **the ledger itself**.
The ledger outlives the tooling.

---

## 6. States and transitions (**canonical**)

### States

**The "always carries" column lists only what is added to the common holdings of §4, and what must not be carried.**

| State | Carries in addition | Must not carry |
|---|---|---|
| **作られた** `Created` | — | Assignee |
| **着手できる** `Ready` | — | Assignee, approval |
| **実行中** `InProgress` | Assignee | Approval |
| **答え待ち** `AwaitingAnswer` | Assignee (the question's body is canonical in the event `QuestionAsked`) | Approval |
| **提出済み** `Submitted` | Assignee. **The result's location is not empty** | Approval, the check's outcome |
| **承認待ち** `AwaitingApproval` | **The assignee is an `Owner`** (I6), the result's location | Approval |
| **承認済み** `Cleared` | **Approval**, the result's location | — |
| **失敗した** `Failed` | **What fell over** | Assignee |
| **終わった（確かめ待ち）** `FinishedPendingRecheck` | Approval, **recheck date** | The evidence's location |
| **終わった** `Finished` | Approval. **The evidence's location is not empty.** **Terminal** | — |
| **打ち切られた** `Abandoned` | Who abandoned it, **the reason**. **Terminal** | — |

### Transitions

**Transitions that cannot happen are not written. The types will not let them be built.**

| From | To | Operation | Events left behind | Who |
|---|---|---|---|---|
| (none) | Created | request `request` | `JobRequested` + `JobCreated` | Human |
| (none) | Created | create `create` | `JobCreated` | Clock |
| Created | Ready | hand out `hand_out` | `JobHandedOut` | Clock |
| Ready | InProgress | start `start` | `JobStarted` | **The AI trying to take it** (not yet the assignee) |
| InProgress | Ready | release `release` | `JobReleased` | The assignee |
| InProgress | Ready | return the timed-out one `return_timed_out` | `JobTimedOut` | Clock |
| InProgress | AwaitingAnswer | ask `ask` | `QuestionAsked` | AI |
| AwaitingAnswer | **Ready** | answer `answer` | `QuestionAnswered` | **Human** |
| InProgress | Submitted | submit `submit` | `ResultSubmitted` | The assignee |
| InProgress | Failed | fall over `fail` | `JobFailed` | AI |
| InProgress | Failed | **hand over to a person** `hand_over` | `AssessmentWritten` + `JobFailed` | AI (**having read that it cannot go further on its own**) |
| InProgress | Failed | **use it all up** `exhaust` | `JobFailed` (the budget was reached) | AI (when `spend` stopped it under I14) |
| Submitted | AwaitingApproval | run the check `run_check` (passed) | `CheckPassed` (and to whom the assignment moved) | Clock |
| Submitted | Ready | run the check `run_check` (stopped, retries left) | `CheckStopped` + `Retried` | Clock |
| Submitted | Failed | run the check `run_check` (stopped, **retries exhausted**) | `CheckStopped` + `JobFailed` | Clock |
| AwaitingApproval | Cleared | approve `approve` | `Approved` | **Human** (the owner) |
| AwaitingApproval | Ready | send back `send_back` | `SentBack` | **Human** |
| InProgress | Ready | send back `send_back` | `SentBack` | **Human** (having read the assessment) |
| InProgress | Abandoned | abandon `abandon` | `JobAbandoned` | **Human** (having read the assessment) |
| Failed | Ready | sort the failures `sort_failures` | `Retried` | Clock |
| Failed | Failed | **hand over to a person** `hand_over` | `AssessmentWritten` | AI (budget reached, retries exhausted) |
| Failed | Ready | send back `send_back` | `SentBack` | **Human** |
| Failed | Abandoned | abandon `abandon` | `JobAbandoned` | **Human** |
| Cleared | Finished | confirm `confirm` (evidence present) | `JobFinished` | Clock |
| Cleared | FinishedPendingRecheck | confirm `confirm` (no evidence) | `JobFinished` | Clock |
| FinishedPendingRecheck | Finished | confirm `confirm` (a quote was obtained) | `JobFinished` | Clock |
| FinishedPendingRecheck | FinishedPendingRecheck | confirm `confirm` (**no quote obtainable**) | `RecheckDatePushed` | Clock |
| FinishedPendingRecheck | Ready | send back `send_back` | `SentBack` | **Human** |

**Every road back leads to Ready** — do not grow the number of things to remember. Going back to InProgress would leave a job whose assignee dropped off while waiting for an answer with nobody to pick it up (the AI comes looking for Ready).

### Operations that change the shape but not the state

Spent going 0 → 3 stays "InProgress." **These do not go in the transition table.**

| The device | How to break it |
|---|---|
| Written as **a function returning the same state type**. It returns the pair (same state, event) | Red if a form that returns only the state can be written |
| The only events that may be stamped outside the transition table are `DueDatePassed` · `SpentIncreased` · `AssessmentWritten` · `DraftDelivered` | Red if an event outside that column can be stamped outside the transition table |

---

## 7. Killing it with types

### Forbidden values

| A value that must not be constructible | What refuses it |
|---|---|
| A zero or negative budget | `Budget` |
| A negative amount spent | `Spent` |
| An empty assignee, an empty name | `Assignee` · `JobId` · `RuleName` |
| A due date earlier than the start | `DueDate` |
| A period of the wrong form | `Period` |
| Evidence with an empty quote | `Evidence` |
| An approval missing who or when | `Approval` |
| A send-back with no reason, an assessment with no reason | `SendBack` · `Assessment` |
| **A version with an empty instruction** | `Version` |
| Making an AI the owner | `Owner` |
| A rule shaped as if an AI had activated it | `Rule` (the "activated by" field takes people only) |

### Forbidden states

| A state that must not be constructible | What refuses it |
|---|---|
| Cleared with no approval | Cleared always carries an `Approval` |
| An ending with neither evidence nor a recheck date | There are only two kinds of ending |
| InProgress with no assignee | InProgress always carries an assignee |
| AwaitingAnswer with no question | Asking always takes a non-empty question (a value) and always stamps `QuestionAsked` (I2) |
| Going back to Ready still carrying an approval | The Ready type carries no approval |
| A rule whose versions shrank | The write reconciles against the previous column of versions |
| An "urgent" flag | **There is no such field.** Urgency is expressed as "the due date is today" |
