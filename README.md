# Troupe

**An autonomous agent that runs the recurring work of a home-care agency — and hands the human back only the judgment.**

A home-care agency lives or dies by paperwork that expires. A physician order lapses and every visit under it becomes unbillable. A plan of care goes unreviewed and the next survey finds it. Nobody forgets these on purpose; they are simply small, recurring, and easy to lose under the day's real work.

Troupe watches for them, does the work, and stops at exactly the point where a human has to decide.

**Live, running on Google Cloud right now:** https://troupe-window-834978405023.asia-northeast1.run.app

Two pulses beat every 60 seconds against a Cloud SQL ledger. Nothing on that page was put there by hand — open it and you are looking at whatever the agent has left for the director to decide.

```
a business rule + the calendar ──→ a job is created, handed out
                                        ↓
                       an AI picks it up on its own (no one calls it)
                                        ↓
              it reads the source, asks Gemini, and either
                 · submits a result, quoting the source as evidence
                 · asks the owner a question, when it cannot know
                 · reports that it is stuck, with an assessment
                                        ↓
                    a machine checks the result against the criteria
                                        ↓
        ┌───────────────────────────────────────────────────┐
        │  APPROVE · SEND BACK · ANSWER · ABANDON           │
        │  — the only things left, and only a human does them│
        └───────────────────────────────────────────────────┘
```

Every one of those steps is an event appended to a ledger. Nothing is overwritten and nothing is deleted, so "what happened, and who decided it" is always answerable.

---

## What this submission actually demonstrates

> **The LLM, the ledger, and the scheduler were all replaced — and `domain/` and `app/` did not change by a single line.**

| pillar | was | is now |
|---|---|---|
| the model | Ollama `gpt-oss:20b`, on a laptop | **Gemini 3.5 Flash** via Vertex AI |
| the ledger | SQLite file | **Cloud SQL for PostgreSQL** |
| the residency | macOS `launchd` | **Cloud Run Jobs + Cloud Scheduler** |
| the window | a PySide6 desktop app | **Cloud Run service** (the hosted URL) |

You can check the claim yourself:

```bash
git diff --stat baseline..pillars-swapped -- domain app   # empty
uv run lint-imports                                       # 6 contracts kept
```

`baseline` tags the last commit before the swap began and `pillars-swapped` tags its completion — every commit in between replaces infrastructure without touching the core. Features added after that point (the patient reference screens) did extend `app/`, and the discipline held in that direction too: the design tables were edited first, the reconciliation suite went red, and the code brought it back to green.

This is not a lucky accident. The design said so before the code existed: *"the mechanism that keeps the AI resident is generic — you buy it"*, *"the tool that calls an LLM is generic — you buy it."* Swapping three of them is the proof that the boundary was real.

---

## Architecture

```
 Cloud Scheduler ──(every 60s)──→ Cloud Run Job  troupe-tick
   create · hand out · check · sort failures · confirm · mark overdue · audit

 Cloud Scheduler ──(every 60s)──→ Cloud Run Job  troupe-agent
   start → consult Gemini → submit / ask / fail → patrol and assess
                                          │
 Cloud Run Service  troupe-window ────────┤     Vertex AI · Gemini 3.5 Flash
   today · schedule · history · search    │        (no API key — workload identity)
   approve · send back · answer · abandon │
                                          ▼
                              Cloud SQL for PostgreSQL
                        jobs · job_events · rules · rule_events
                        results · evidence · questions · assessments
```

Inside the container, dependencies point inward only:

```
  ui  ·  adapters        ← Cloud SQL, Vertex AI, files, clock, screens live here
        ↓
      app                ← application services, ports, DTOs. No business rules.
        ↓
    domain               ← value objects, aggregates, invariants, specifications.
                           No clock, no randomness, no storage, no screens, no outside tools.
```

`domain` cannot import `sqlite3`, `urllib`, `random`, `os` or `time`; `ui` cannot import `domain` at all. These are not conventions — they are contracts checked on every run by `lint-imports`.

---

## The parts worth looking at

**The AI is inside the domain, not outside it.** It is a worker with an assignment, a budget, and a retry limit — not a general-purpose oracle bolted onto a workflow. That is why "which operations may the AI perform" is a table in the design and a folder in the code, rather than a prompt.

**Autonomy means arriving uncalled.** The clock never wakes the agent. The agent has its own beat and comes looking for work — for jobs it can start, and for jobs that have fallen over and need an assessment written for the human.

**The model's word is never evidence.** A result is only finished when a quote can be pulled from the source that backs it. A human's answer to a question does not count as evidence either. If a job finishes without a quote, the clock schedules a recheck and goes back for one.

**The model declares its own mark; the domain checks it.** The anti-corruption layer asks the model to prefix its reply with `MARK: RESULT`, `MARK: QUESTION` or `MARK: NEITHER`, strips it, and hands a typed `Reply` inward. Whether to *believe* the mark is a specification in `domain` — never the adapter's call. An unreadable mark falls back to `NEITHER` rather than guessing.

**A runaway agent hits a wall, not a bill.** Every job carries a budget in calls and seconds and a retry limit, copied from the rule version at creation. Crossing either ends the job and puts it in front of a human with an assessment attached.

**Business rules are data, not code.** The three care workflows in `custom/` are JSON plus a text source. Swapping the entire domain of work — from a software team's dependency review to a home-care agency's compliance calendar — took no code change at all.

---

## How the design is kept honest

The five design documents in [`設計/`](設計/) are the source of truth, and they are written in Japanese — that is the language the design was thought in. What matters is that they are not decoration: **the test suite reads them and fails when the code and the documents disagree.**

| what is checked | against |
|---|---|
| the state machine (states, transitions, terminal states) | the transition table in the design |
| every domain event | the events table |
| every value object | the value-object list |
| every application service and its port | the operations table and the interface table |
| the glossary bridge shown in the web UI | the glossary table |

Edit one row of a table in a design document and the suite goes red. Edit the code without the document and it goes red too. There is no way to let them drift quietly.

On top of that, `tests/break_check.py` removes each of the **66 obligations** in the domain one at a time and asserts the suite goes red for every single one — a check that the safety net is actually attached, not just present.

```bash
uv run pytest -q            # 737 tests
uv run pyright              # domain and app are strict
uv run lint-imports         # 6 dependency contracts
uv run python tests/break_check.py
```

---

## Running it

**On Google Cloud** — one script wires everything and is safe to re-run:

```bash
sh cloud/deploy.sh          # service account, Cloud SQL database, image, jobs, service, schedules
sh cloud/status.sh          # ledger, window, last beat of each pulse, recent logs
sh cloud/teardown.sh        # removes the pulses and the window — never the ledger
```

It needs a Google Cloud project with billing, and these APIs enabled: `aiplatform`, `run`, `sqladmin`, `cloudscheduler`, `artifactregistry`, `cloudbuild`, `secretmanager`. The runtime service account holds `aiplatform.user`, `cloudsql.client`, `run.invoker`, `secretmanager.secretAccessor` and `logging.logWriter` — **no API key exists anywhere**; Gemini is reached with the workload's own identity.

**On a laptop**, with nothing cloud at all — the same code, different things poured in:

```bash
uv run python main.py rule-add --name "Survey Readiness Check" --by Director
uv run python main.py rule-activate --name "Survey Readiness Check" --version 1 --by Director
uv run python main.py tick
uv run python main.py --llm gemini agent --name Nomi
uv run python main.py serve --viewer Director        # the same window, on localhost
uv run python main.py window --viewer Director       # the desktop window
```

`--llm ollama|gemini` picks the model, `--dsn` picks the ledger. Everything else is identical.

---

## A note on the data

Every patient, clinician, practice and document in `custom/` is **invented**. "Riverbend Home Health" does not exist. No real health information appears anywhere in this repository, and the agent is never given any. The workflows are real; the data standing in for them is not.

## A note on judgment

Troupe will not approve its own work, and it cannot be configured to. Approving, sending back, answering and abandoning are the four operations the design places on the human side of the line, and there is no code path that reaches them from the agent. That is the whole point of the thing: an agent that does the work, and a person who stays responsible for it.

---

Japanese README: [README.ja.md](README.ja.md) · Design documents (Japanese): [`設計/`](設計/)
