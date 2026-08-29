# Troupe (Ichiza) — How work moves

**Version**: v2.0 (2026-08-22)
**Role**: Who raises what. Where the judgment sits. What is taken in and put out. **It closes here.**

[What a job is](what-a-job-is.md) covers "what it carries"; this sheet covers "how it moves."

> **This file is a translation.** The source of truth is [`設計/仕事が回る筋道.md`](../設計/仕事が回る筋道.md). The reconciliation tests read the Japanese file — the operation tables in §1, the interface table in §4 and the events table in §5 are parsed straight out of it — not out of this one. Where the two disagree, the Japanese is right.

---

## 1. Who starts things

**Four kinds. They are split so the line the axiom draws can be read straight off a list.**
Only the human's share is judgment; neither the AI's share nor the clock's is.

### What a person starts — **only here is there judgment**

| Operation | Identifier | What it does |
|---|---|---|
| Request | `request` | Reads the request and creates a job |
| Approve | `approve` | Grants the approval that was offered. **The owner only** (I6) |
| Send back | `send_back` | Returns it to Ready with a reason |
| Answer | `answer` | Answers the question. **An answer is not evidence** — evidence is taken from the source |
| Add a version | `add_version` | Appends a version **from the topic's data read as defaults, with the person's overwrites** |
| Activate | `activate` | Decides that this version may give birth to jobs |
| Deactivate | `deactivate` | Decides to **stop** giving birth to jobs from this version. The active version number goes back to empty — **the column of versions is untouched** (append-only) |
| Agree a recurring visit | `add_pattern` | Puts the recurring-visit agreement arranged with the patient (weekday, **interval in weeks**, clinician) into the medical record. **The agreement is the judgment** — everything downstream of it is machinery |
| End a recurring visit | `end_pattern` | Puts an end date on the agreement and **drops the not-yet-arrived visits it produced to cancelled** (bookkeeping the judgment — unwinding the expansion). **The column is never deleted** |
| Sign and end the visit | `sign_note` | Appends the S/O/A/P the person wrote on top of the draft into the medical record as a **signed record** and drops the visit to done (**one transaction in the medical record**). Nothing is written to the draft — **whether it was used is derived from the existence of the record that (patient, visit date) binds**. **The signer is the seat that pressed it** — there is no path by which the seat and the signer differ. **Making this record a fact is the judgment** — it is not written to the ledger (the chart's canonical home is the medical record) |
| Skip this visit once | `cancel_visit` | Drops only that one planned visit to cancelled, with a reason. The agreement stays alive — **deciding with the patient not to go this time is the judgment** (the one-off form of `end_pattern`; a done visit cannot be dropped) |
| Add a service | `add_service` | Puts the services and drugs performed that day (rows of the fee schedule) and their quantity onto a visit that is not yet signed. **Signing freezes it** — there is one gate for facts |
| Remove a service | `remove_service` | Removes one service row from a visit that is not yet signed |
| Rule on a flagged row | `resolve_charge` | Takes a charge row the machine flagged and either **passes it with a reason** (the exception to the cap — the text copied onto the claim) or strikes it. **Applying the exception is exactly the judgment** |
| Confirm the monthly claim | `confirm_claim` | Makes one patient's claim for one month a fact (after the month has ended). **A confirmed claim and its charge rows cannot be rewritten** (a lock in the medical record) — the file for the payer and the patient's invoice are copies of that confirmation |
| Abandon | `abandon` | Sends a job that can no longer be pursued to a terminal state, with a reason |

### What the AI starts

**The trigger is the AI itself. It stays resident and comes looking for two things.**

1. Jobs that are **Ready** — take one and move it along
2. Jobs that **need a human hand** (**budget reached, retries exhausted**, recheck date arrived, **finished with no evidence**) — **write an assessment**

Without the second, **fallen jobs get no assessment**. "Wake the AI" is not put on the clock —
**autonomy is arriving uncalled**. The mechanism that keeps it resident is generic (bought).

| Operation | Identifier | What it does | Why it is not judgment |
|---|---|---|---|
| Start | `start` | Takes a Ready job into InProgress — **assembling the material (answered questions and so on) is `consult`'s work** | Whether it can be taken is decided by the type |
| **Consult the LLM** | `consult` | Reads the source (**if it cannot be read, on to `fail`**), hands it to the LLM, and receives **a `Reply` plus the calls and seconds used**. Adds to the amount spent, **lets the specification route it**, and returns a question, a result or an assessment | **The specification routes it.** This operation only carries |
| Ask | `ask` | Appends the question and moves to AwaitingAnswer | **It does not ask for a judgment.** Only for missing material |
| Submit | `submit` | Appends the result. **If reading the source again yields a quote**, appends the evidence too. If not, submits without evidence | It does not decide pass or fail |
| Fall over | `fail` | Leaves behind what fell over | It only records what happened |
| Use it all up | `exhaust` | Records that the budget was reached and goes to Failed | A number merely touched its limit |
| Release | `release` | Drops the assignment and goes back to Ready | It is not a decision to give up |
| Write an assessment | `assess` | Appends what was read and why. **It can be written even when not the assignee** (the exception to I13) — fallen and finished jobs are exactly where an assessment is needed. **It does not change the state** (`hand_over` writes the assessment and then drops to Failed) | **A report of fact and a proposal. The person decides** |
| Hand over to a person | `hand_over` | When **the specification says** it can go no further on its own, writes the assessment and waits for a human judgment. **The body of the assessment is placed as what fell over, verbatim** | **A report of the fact that it cannot proceed.** What to do about it is the person's call |
| Add to the amount spent | `spend` | Adds the calls and seconds the LLM call cost. **Called inside `consult`** | It only counts. It stops at the budget (I14) |
| Patrol | `patrol` | Goes looking for jobs that need a human hand and writes assessments (**the enforcer of I15**). Hands over the ones stuck in progress | Whether to write is decided by the specification |

### What the screens start

**They run only when a person opens a screen. Nothing is written to the ledger.**

| Operation | Identifier | What it does | Why it is not judgment |
|---|---|---|---|
| Gather today | `gather_today` | Gathers what needs this person's eyes and judgment right now | **The specification decides.** This gathers and hands over |
| Gather the detail | `gather_detail` | Gathers everything about one item (events, questions and answers, assessments) | Same |
| Gather the schedule | `gather_schedule` | Gathers the list of rules with their next periods and what has not been created, plus **the column of created jobs (all but the terminal ones)** | Same. `reconcile` decides what is uncreated |
| Gather the history | `gather_history` | The column of events, newest first, **with the heading of the job it belongs to** | Read-only. Writes nothing |
| Search | `gather_search` | Pulls job rows by the filter conditions — **finished ones included** | Same. **The state word → identifier bridge is here** |
| Gather the route | `gather_route` | Lines up that day's planned visits per clinician, nearest-from-base first | Only comparisons of distance. It lines them up and hands them over |
| Gather the visit | `gather_visit` | Copies the material for one visit's bedside entry (patient summary, unused draft, signed records, roster of clinicians) | Read-only. **Not translated into our words** |
| Gather the agreements | `gather_patterns` | Copies the list of agreements | Read-only. Writes nothing |
| Gather the patients | `gather_patients` | Copies the patient list from the medical record (**another bounded context**) | Read-only. **Not translated into our words** |
| Gather one patient | `gather_patient` | Copies one person's chart extract (prescriptions, physician orders, plans, events, records) | Same |
| Gather seats and roles | `gather_staff` | A copy of the staff register (seat name and role) — used for choosing who you are and for deciding what can be pressed | Read-only |
| Gather the billing | `gather_billing` | Gathers the copy of month × patient charge rows, flags and claims | Read-only. Counts and points are copied, not computed |
| Gather the fee schedule | `gather_fees` | A copy of the fee-schedule master | Same |
| Answer on the guide | `ask_guide` | Hands the person's question and **the copies the screens already gathered** to the LLM and receives the text of an answer. Nothing is written to the ledger | **The LLM composes the answer. It only guides — the person presses** (it receives no tool that reaches execution) |
| Gather now | `gather_now` | A copy of the ledger's now — the count per stage (queued · working · checking · waiting), the jobs being worked on, when the clock last wrote. The raw feed (SSE) is just the shell repeating the same read — a derivation left open | Read-only. **No forecasts — only the fact of the last beat** |

**Do not put these on the clock.** Doing so needs somewhere to put the outcome, and that means **storing a decision that is not stored**.
Screens are always derived — they look at the ledger at the moment they were opened.

### What the clock starts

**It runs with nobody calling it. Running it again gives the same result** — `confirm` is the exception, because it reads the source.

| Operation | Identifier | What it does | Why running it again is the same |
|---|---|---|---|
| Create | `create` | From the active versions and now, creates the jobs that do not exist yet. **A version whose source carries a `{患者}` (patient) hole gets one job per planned recurring visit within the lead (the version's days)** — the `{患者}` and `{訪問日}` (visit date) holes are opened at copy time, and the origin key takes the patient and the visit date (**the version and the period stay out of the key** — a version change never creates a second job for the same visit) | Origin is unique (I3) |
| Hand out | `hand_out` | Moves created jobs to Ready | It does not touch what has already been handed out |
| Return the timed-out | `return_timed_out` | Drops assignments that ran past their limit | It does not touch what has not run out |
| Run the check | `run_check` | Looks at the result body against the acceptance criteria. **If it passes, moves the assignment to the owner** | **The same result gives the same outcome whenever it runs** (`{対象期間}` was already opened out at copy time) |
| Sort the failures | `sort_failures` | **If the retry count has not reached the limit and the amount spent has not reached the budget**, retry. If either has, leave it | Only comparisons. **The job carries all four** — the Store is never asked |
| Confirm | `confirm` | **If the evidence's location is not empty**, finish. If it is empty, read the source again; if a quote comes, append it and finish. If not, **push the recheck date forward** | Appended evidence is always complete (the obligation on `Evidence`). **It reads the source, so this is the one place the outcome can change** |
| Mark overdue | `mark_overdue` | Leaves a mark, once, on a job past its due date | Only a comparison of dates |
| Audit | `audit` | For each active version, counts whether a job exists for the current period (for a holed version, **per planned visit within the lead**) (**the cyclic reconciliation of I8**) | **Read-only.** Writes nothing |
| Plan the visits | `plan_visits` | From the active recurring agreements, creates the future visits in the medical record if they are not there yet. **Expanding an agreement is bookkeeping** — the same shape as `create` making jobs from version × calendar | Origin is unique (agreement × date — a unique key in the medical record) |
| Derive the charges | `derive_charges` | From signed visits and the record of services, creates that day's charge rows and the monthly claim draft in the medical record **if they are not there yet** (weeks start Sunday and are counted across month boundaries; the same building counts from two people on one day; the monthly tier comes from visit count × severity × people in the building — **the values of those rules live in the fee-schedule master**). Computing points and counting visits is not judgment — **a row that touches a cap is placed as a 0-point flag** and a person rules on it. **Only machine rows may be re-placed** (rows a person touched and confirmed months are never touched) | Origin is unique (visit × service key, patient × month key) |
| Deliver the drafts | `deliver_drafts` | Places approved chart drafts into the medical record **as drafts only, addressed to their visit (patient · visit date)**. When placed, **stamps `DraftDelivered`** — delivery is a fact that stays in the ledger (F4) | Approval is already done. It only carries — **it carries only what has no mark** (the (patient, visit date) unique key is the second guard) |

**The draft promise (SLA)**: a recurring visit that is in the medical record by 00:00 JST two days before its date D has, **by 00:00 JST on D**, an unconsumed draft whose body carries the exact D. The staleness cap = the lead days + the visit hour. A visit added late is **born overdue** — the red mark is the delay made visible, not a malfunction. Urgent house calls are outside the promise (best effort, nothing more).

### The values received from a person

What crosses from screen to app is **text only** — app assembles what the person wrote into values. **Without a field to receive it, pressing produces no value.**

| Operation | What the person writes |
|---|---|
| Answer | The body of the answer |
| Send back | The reason |
| Abandon | The reason |
| Request | The request body, the source, the required terms (**those three the person writes**). The rest is defaulted if left blank — **instruction = the request body, owner = the requester**, cycle = weekly, days = 3, budget = 20 calls / 600 seconds, retries = 2 |
| Add a version | Instruction, source, acceptance criteria, cycle, days, budget, owner, max retries |

### Rules

- **They hold no business rules.** The moment you want an `if` that judges the business, it belongs in an aggregate or a domain service
- **One job = one transaction.** The boundary is held here
- **Always name who appends.** A store with only readers stays empty forever
- **Always name who moves a number.** A number nobody increments stays 0 forever

**This section is canonical for the counts.** If one of them grows out of proportion, judgment has drifted — more human ones means too much toil, more AI ones means it decides too much, more clock ones means it moves too automatically, more screen ones means every opening gets heavier.

---

## 2. Where the judgment sits — domain services and specifications

**Both are domain. They never open the ledger and never write to it. They take material and return an answer.**
The application service is what writes.

### Domain services — business judgments that belong to no aggregate

**How to spot one**: two or more aggregates appear in the arguments, and the return value is none of them.

| What it judges | Identifier | Material | Why it is not inside an aggregate |
|---|---|---|---|
| What should be created now | `reconcile` | The column of (id, number, cycle, source, **days**) for active versions + the column of origin keys that already exist + **the column of planned recurring visits (patient code · visit date)** + **now**. A holed version is judged not by the period but by **the visit's approach** (today JST ≤ visit date ≤ today + days) | It straddles both rule and job |
| Which jobs need **this person's** eyes and judgment now | `judge_today` | The gathered material for today + **each one's column of pressable operations** + **now** | It belongs to no single job |
| └ **The call order is today's material → what can be pressed → judge_today.** A row with nothing pressable is not returned |

**`reconcile` also decides the period.** It produces a `Period` from the cycle and now —
that is a business judgment, so it cannot live in app.

### Specifications — predicates that settle black and white

| What it asks | Material | Answer |
|---|---|---|
| Does the result meet the acceptance criteria? | The result body + the **required terms** of the acceptance criteria | Passes / stops, with a reason. **Literal matching only** — which is why it gives the same outcome every time |
| Is the approval offered the owner's? | The job + **the approval offered** | True or false (I6) |
| Which operations may **this person** press on this job now? | **Today's material** (**domain values**; the canonical field list is [what people see §2](what-people-see.md)) + **the person looking** + **now** | The column of operations. **It never returns an operation absent from the transition table** |
| **Where does this `Reply` get routed?** | **The `Reply` (mark and body)** + the **required terms** of the acceptance criteria | If the mark is question, to **question**. If the mark is result and the body **contains every required term, to result**. **If it does not, to assessment** — **this is where the declaration is examined**. If the mark is neither, to **assessment** |
| **Can it go no further on its own?** | The body of the previously submitted result + the column of reasons it stopped + the retry count | If true, `hand_over` (from InProgress) |
| Which operations may **a person** press on this rule now? | Whether an active version exists | Add a version and activate, any time. **Deactivate only while an active version exists** |
| **Should an assessment be written on this job now?** | The assessments so far + the column of what fell over and why it stopped + **the amount spent and the budget** + **the retry count and the retry limit** | True or false (F6 — **never write the same assessment twice**). **Always true when the budget was touched or the retries are exhausted** (I15) |

**Routing the LLM's response is a business judgment** (I16). adapters only shape it.
The calls and seconds used are not something to translate — `LlmPort` returns them separately from the response.

### The measuring stick for telling them apart

| Shape | What it is | Where it lives |
|---|---|---|
| `X → X` | An operation on an aggregate | Next to that aggregate |
| `parts → boolean` | A specification | domain |
| `several aggregates → a decision` | A domain service | domain |
| `ledger → a write` | An application service | app |

**Domain services are an escape hatch.** When in doubt, **first ask "who is the subject of this operation."**
If some aggregate can be the subject, make it that aggregate's operation.

### Policy

**The version carries "what should be done" as data, and a person activates it. It is not code.**

| What a version carries | What it produces |
|---|---|
| Instruction `Instruction` | **What the AI does** |
| Source `Source` | Where the AI reads |
| Acceptance criteria | What the check looks at |
| Cycle | When, and for which period, jobs are created |
| Days until due | The due date |
| Budget | Where it stops |
| Owner | Who approves, and who receives the questions |

**Nothing you write in a version can break an invariant.**

---

## 3. Factories — creation and reconstruction

**To guarantee that only things satisfying the invariants are born.** Not to hide `new`.

### Creating a job

| Holding | What decides it |
|---|---|
| `JobId` | **Whoever raises it assigns it** (numbering lives outside the factory) |
| `Origin` | For a rule-born job, `RuleName` + version number + `Period`. **For a visit job from a holed version, `RuleName` + patient code + visit date** (the version and the period stay out of the key). For a requested job, the request's id |
| The version it was born from | Fixed at creation |
| What is copied from the version | **Every common holding in [what a job is §4](what-a-job-is.md)** (canonical there) |
| `DueDate` | **The start time + the version's days** (for a requested job the request's time; for a rule-born job the time it was created). **A visit job is due at 00:00 JST on the visit date** — the SLA's deadline itself (the overdue mark becomes the detector of a broken promise) |
| `Spent` | `Spent(0, 0)` |
| Initial state | Created |

**The version itself is never handed over.** The `Rule` aggregate returns "the bundle that gets copied" (the common holdings + days until due), and the days become the `DueDate` and disappear.

### Creation and reconstruction are entirely different

| | Creation | Reconstruction |
|---|---|---|
| When | When a new item is born | When reading back from the ledger |
| Business rules | **Applied** (the table above is the rule) | **Must not be applied** |

**Applying today's rules on reconstruction rejects yesterday's rows by today's rules.** All that is applied is the shape of the types — if it does not match, it says "cannot read this, pour it in again" and stops. **An old ledger may be thrown away** — pour it in again and it comes back. What is not acceptable is breaking quietly.

---

## 4. interfaces (**canonical**)

**The suffix states the role. This table and the four tables in §1 are held by the reconciliation tests** — names against identifier ↔ file, declarations against location, requesters against the imports.

| interface | Suffix | What it takes in and puts out | Declared in | Implemented in | Requesters |
|---|---|---|---|---|---|
| `JobRepository` | Repository | One job aggregate root by key | domain | adapters | Aggregate: job (I1) / every write |
| `RuleRepository` | Repository | One rule aggregate root by key | domain | adapters | `create` · `add_version` · `activate` · `deactivate` (**`run_check` looks at the criteria the job copied**) |
| `RuleReader` | Reader | The list of rules (name, version number, active version, instruction — **the instruction of the active version, or the latest if there is none**) | **app** | adapters | `gather_schedule` |
| `ResultStore` | Store | Appends results | domain | adapters | Appends: `submit` / reads: `run_check` (**screen reads go through a Reader — one carrier only**) |
| `EvidenceStore` | Store | Appends evidence | domain | adapters | Appends: `submit` · `confirm` / reads: `confirm` (**same**) |
| `ClockPort` | Port | Gives the current time | **app** | adapters | **Every human, AI and clock operation**, plus `gather_today` · `gather_detail` · `gather_schedule` (history and search need no "now") |
| `IdPort` | Port | Assigns a new identifier | **app** | adapters | `request` · `create` |
| `LlmPort` | Port | Hands things to the LLM and receives **a `Reply` (with its mark) plus the calls and seconds used**. **For the patrol it has the situation read and returns the body of an assessment** — without assessments the AI can only give numbers. **The assessment call is not counted against the budget** (the safety valve exists to stop a runaway that moves work along; a runaway of assessments is stopped by F6) | **app** | adapters | `consult` · **the patrol** |
| `SourcePort` | Port | Reads from the source. **Translates the source's words into business words** (the anti-corruption layer, ACL). There are two exits — **the quote, and the reason it could not be read**; what was read is covered by the quote (**an exit with nobody to return it is not created**) | **app** | adapters | `consult` · `submit` · **`confirm`** (taking the evidence quote) |
| `TopicPort` | Port | Reads the topic's data (the contents of a version) | **app** | adapters | `add_version` |
| `ActiveRuleReader` | Reader | Reads (id, number, cycle, source, **days**) of active versions — the same shape as `reconcile`'s material | **app** | adapters | `create` · `audit` · `gather_schedule` |
| `ScheduledVisitReader` | Reader | Copies the medical record's planned **recurring** visits (patient code · visit date, kind=regular) **as text** — the material for expanding a holed-source version. Whether one has approached is `reconcile`'s call | **app** | adapters | `create` · `audit` · `gather_schedule` |
| `OriginReader` | Reader | Reads the origin keys of existing jobs | **app** | adapters | `create` · `audit` · `gather_schedule` |
| `WorkReader` | Reader | **Only the material the AI needs for one job that lives outside the aggregate** — answered questions, the body of the previously submitted result, **the column of what fell over and why it stopped**, the assessments so far, **the states of jobs born from other versions with the same `RuleName` and the same `Period`** (instruction, acceptance criteria, source, amount spent and budget, recheck date are **carried by the aggregate** — do not create a second canonical home) | **app** | adapters | `consult` · `patrol` |
| `JobStateReader` | Reader | The ids of jobs in a given state. **Can also filter by assignee** | **app** | adapters | `start` · `patrol` · `hand_out` · `return_timed_out` · `run_check` · `sort_failures` · `confirm` · `mark_overdue` (**counted by the name of whoever is injected with the declaration**) |
| `OverdueMarkReader` | Reader | The ids of jobs already marked "past its due date" — the check that prevents stamping twice | **app** | adapters | `mark_overdue` |
| `TodayReader` | Reader | **Today's material** (the domain values the specification looks at; the fields are today's row in [what people see §2](what-people-see.md) minus what can be pressed). **It can pull a single item** — terminal ones included (the detail screen looks at finished jobs too. **Only the list read never carries terminal ones** — nothing terminal appears on Today) | **app** | adapters | `gather_today` · `gather_detail` |
| `DetailReader` | Reader | The material for the detail — **only the column of events and the whole column of question-and-answer pairs**. Results, evidence and assessments are carried by today's material (**one carrier only**) | **app** | adapters | `gather_detail` |
| `HistoryReader` | Reader | Event rows newest first — **with the job id and the material for its heading** (`RuleName`, period, instruction). **It can also state the total** (never show a list whose size is unknowable) | **app** | adapters | `gather_history` |
| `SearchReader` | Reader | Pulls job rows by the filter conditions (**states mapped to identifiers first**) — **finished ones included** (F1) | **app** | adapters | `gather_search` |
| `PatientReader` | Reader | Pulls the medical record's patient rows and chart extracts **as text and IDs** — **a copy from another bounded context; not translated into our words** (a patient never becomes a Troupe aggregate — it is outside the boundary) | **app** | adapters | `gather_patients` · `gather_patient` |
| `EmrDraftPort` | Port | Places an approved draft, as (job id · patient · visit date · body), **into the medical record's drafts inbox only** — **once per (patient, visit date)**. There is no port that writes a signed record (final). Returns whether it could be got into the inbox (false if it did not arrive — the next beat comes again) | **app** | adapters | `deliver_drafts` |
| `EmrPatternPort` | Port | Puts a recurring agreement into the medical record, ends one, reads them. **Called only by human operations** | **app** | adapters | `add_pattern` · `end_pattern` · `gather_patterns` |
| `EmrSchedulePort` | Port | Reads active agreements and the keys of existing plans, and creates **only agreement-derived visits** in the medical record — there is no port that writes urgent, cancelled or signed ones | **app** | adapters | `plan_visits` |
| `RouteReader` | Reader | Pulls that day's planned visits per clinician, with the patients' coordinates and **how the draft stands** | **app** | adapters | `gather_route` |
| `EmrVisitPort` | Port | Ends that day's visit — **appends the signed record and moves the visit to done** (one transaction in the medical record) / **cancels just this once, with a reason**. **Called only by human operations.** There is no port that rewrites or deletes an appended record | **app** | adapters | `sign_note` · `cancel_visit` |
| `VisitReader` | Reader | Pulls one visit's bedside material (patient summary, unused draft, signed records, roster of clinicians) **as text and IDs** | **app** | adapters | `gather_visit` |
| `DeliveredMarkReader` | Reader | The ids of jobs already marked "the draft was delivered" — the check that prevents carrying twice | **app** | adapters | `deliver_drafts` |
| `FeeReader` | Reader | Copies the fee-schedule master rows **as text and IDs** | **app** | adapters | `gather_fees` |
| `EmrServicePort` | Port | Puts services on a visit that is not yet signed, and removes them. **Called only by human operations** | **app** | adapters | `add_service` · `remove_service` |
| `EmrChargePort` | Port | Derives charge rows and a claim draft from signed visits and their services and places them. **There is no port that rules on a flag or confirms** — and no path that writes into a confirmed month | **app** | adapters | `derive_charges` |
| `EmrClaimPort` | Port | Passes or strikes a flagged row with a reason; confirms one patient's claim for one month. **Called only by human operations.** There is nowhere a port that rewrites a confirmation | **app** | adapters | `resolve_charge` · `confirm_claim` |
| `BillingReader` | Reader | Copies month × patient charge rows, flags and claims **as text and IDs**. **It can also state the total number of flags awaiting a ruling** (never show a mark whose count is unknowable) | **app** | adapters | `gather_billing` |
| `StaffReader` | Reader | Copies the staff register (seat name, role = director / clinician). **The canonical home of a role is data** — the medical record's staff and clinicians (the roster of doctors). **A seat is a claim of name, not authentication** (all authority comes from the register's gates) | **app** | adapters | `gather_staff` |
| `GuidePort` | Port | Hands over the person's question and the copies (text) and receives **the text of an answer**. **One call outside any job** — the amount spent is added to no job (there is no job to add it to). Runaways are stopped by rate limits (question length, a cap on exchanges — `ask_guide` cuts it off). **It receives no writing tool — there is no path in the types from the guide to execution** | **app** | adapters | `ask_guide` |

### Rules

| Rule | Why |
|---|---|
| **A Store's "append" returns the location** | Assigning the location elsewhere makes two parties, one assigning and one appending |
| **One Repository per aggregate root. It returns the aggregate root only** | Letting parts out means they get rewritten outside the boundary |
| **A Repository takes a key and returns one. Lists and filters are Readers** | The screen's convenience never gets into the centre's interfaces |
| **A Reader never writes. The return types of Readers and Ports are decided by where they hand to** — text and IDs to screens and the LLM, **domain values to domain specifications** (`TodayReader` → today's material, `LlmPort` → `Reply`). Even when declared in app, if the return type is domain, **the dependency still points inward** | Making the material for a decision an app type would have domain look at app |
| **Ports never appear in domain** | Outside tools carry no invariant one can point at |
| **No interface is created with an empty requester column** | Declarations nobody calls were what grew most last time |
| **No Store is created with an empty appender** | Its contents stay empty forever (which is what happened to evidence) |
| **No section called "not yet placed" is created** | The reason for not placing it ("X is not in the list") can vanish unnoticed. **Four of them really did survive with their reason gone** |
| **Questions, answers and assessments have no Store — the events are canonical** (`QuestionAsked` · `QuestionAnswered` · `AssessmentWritten` carry the full bodies; reads go through `WorkReader` and `TodayReader`) | Writing the same value into both a table and an event means one gets fixed and the other drifts |

### Dependency inversion

domain declares "what can be taken in and put out" as types, and adapters implement them inward.
**A device whose only purpose is to turn the arrow around.**

### The write gate

**Make a shape that cannot be called with the state alone.** The argument is one pair: "**the new state, and the column (non-empty) of domain events giving its reason**."
An empty column cannot be constructed in the first place — that is I1 made real. It is a column because one transition can leave two events
(request = `JobRequested` + `JobCreated`).
**Optimistic locking never leaks out of the port.** All that comes back is "written / not written."

---

## 5. Domain events (**canonical**)

**Past tense. Observation only. No judgment. Append-only.**

**Every event carries "when" and "who."** Who = `Actor` (human, AI, clock).
The table below lists only **what is left in addition to that** — writing the common parts per event drops one somewhere. The obligations on what is left are the same as for values (an empty reason, an empty body, an increase of 0 cannot be left). **Bold (a person is the subject) means the type of `by` is a person** — the reconciliation test holds that.

| Event | What is left behind | Identifier |
|---|---|---|
| A job was requested | Who, and what | `JobRequested` |
| A job was created | Which rule, which version, which period | `JobCreated` |
| A job was handed out | — | `JobHandedOut` |
| It was started | Who took it | `JobStarted` |
| It was released | Who let go | `JobReleased` |
| It came back on timeout | Whose assignment it was | `JobTimedOut` |
| A result was submitted | The result's location + **the evidence's location** | `ResultSubmitted` |
| The check passed | **To whom the assignment moved** | `CheckPassed` |
| The check stopped it | The reason it stopped | `CheckStopped` |
| **It was approved** | — | `Approved` |
| **It was sent back** | Who, and the reason | `SentBack` |
| It finished | The evidence's location, or the recheck date | `JobFinished` |
| The recheck date was pushed forward | The new recheck date | `RecheckDatePushed` |
| **It was abandoned** | Who, and the reason | `JobAbandoned` |
| It passed its due date | — | `DueDatePassed` |
| A draft was delivered | — (where it was placed is known to the source) | `DraftDelivered` |
| It failed | What fell over | `JobFailed` |
| It was retried | Which attempt this is | `Retried` |
| The amount spent increased | The calls and seconds added | `SpentIncreased` |
| A question was asked | What | `QuestionAsked` |
| **It was answered** | Who, with what + **whose assignment came off** | `QuestionAnswered` |
| **An assessment was written** | What was read, and why it was read that way | `AssessmentWritten` |
| A version was added | Which version | `RuleVersionAdded` |
| **A rule was activated** | Who, and which version | `RuleActivated` |
| **A rule was deactivated** | Which version was stopped | `RuleDeactivated` |

**Bold means a person is the subject.** This is "judgment is human" made real.
**An assessment has the AI as its subject and is still not a judgment** — it is a report of fact and a proposal; the person receives it and decides.
