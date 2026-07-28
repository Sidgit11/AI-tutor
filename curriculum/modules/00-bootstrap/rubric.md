---
module: 00-bootstrap
rubric: 00-bootstrap-gate
gate_type: oral defense + repo evidence
---

# Module 0 Gate — Rubric

**Gate type: oral defense.** There is no code to execute, so this gate is administered as a live viva plus verification of repo evidence. Every criterion below is observable — either an artifact exists in the repo, or a question is answered correctly, cold.

**Cold means cold.** Questions are answered from memory, without the files open. Explaining `mastery.json` while reading `mastery.json` demonstrates literacy, not knowledge. The defense is one continuous sitting; you do not get to go look something up and come back.

**Scoring is per criterion: `pass` or `fail`.** All eight pass → gate pass. Any one fails → gate fail, with the failed criteria becoming the remediation plan. There is no weighting and no partial credit; "almost" is a fail with a precise description of the gap.

---

## Criteria

### C1 — A complete session loop is on disk

**Observable:** `student/journal/` contains at least one entry recording what was covered, escalations if any, and a next-session seed. `student/mastery.json` shows ≥ 1 concept with a non-empty `evidence` array whose strings are factual and specific (cite a rep, a grade, or a teaching pass — not "went well"). `state.json.last_closed` is populated and `session.active` is `false`. `streak.count` ≥ 1.

**Fails if:** the journal entry is missing the next-session seed; evidence strings are evaluative rather than factual; the session was never properly closed.

### C2 — Resume-from-checkpoint demonstrated live

**Observable:** The candidate interrupts a live session mid-phase, then restarts. `/standup` detects `session.active: true`, offers resume-or-restart rather than starting fresh, and resumes from the checkpoint that was in `state.json` at the moment of the interrupt.

**Fails if:** the tutor starts fresh without offering resume; the resumed position does not match the checkpoint; the checkpoint was too vague to resume from and the tutor guessed. *(Note: a vague checkpoint is a fail of this criterion even though the tutor wrote it — the candidate is responsible for running sessions in which checkpoint discipline is upheld, and for logging it as a defect when it isn't.)*

### C3 — Architecture explained cold: the agents

**Observable:** Names all four agents, states what each owns and what each may write to, and correctly identifies which two are active in v0.1 and which two are staged with their activation triggers.

**Fails if:** any agent's ownership is misattributed; the candidate cannot say what the director owns; staged agents are described as active.

### C4 — Why the grader is a separate agent

**Observable:** Explains that a single agent carries the teaching conversation in its context, so effort and sympathy contaminate judgement; that the grader is spawned with a **fresh context** receiving paths only; that it **executes** rather than reads; and that the all-pass-or-fail arithmetic removes negotiation. Must articulate the general principle: capability boundaries, not instructions — *"it cannot"* beats *"I told it not to."*

**Fails if:** the answer is only "so it's more objective" without the mechanism; the candidate cannot say what the grader is and isn't given at spawn time.

### C5 — `mastery.json` explained field by field

**Observable:** Names every top-level key (`meta`, `concepts`, `gates`, `escalations`, `mode_counts`, `streak`) and states what each is for. Within `concepts`, explains `mastery`, `last_touched`, `next_review`, `evidence`, `misconceptions`. Correctly states **why `next_review` is null everywhere** (the examiner is v0.2 and owns that field). Explains why teaching alone caps mastery around 0.4–0.5 and what raises it beyond that.

**Fails if:** any top-level key cannot be explained; the mastery-score asymmetry is not understood; `next_review` being null is attributed to an oversight.

### C6 — `state.json` and checkpoint discipline

**Observable:** Explains every field including the `phase` enum and `parking_lot`. States that the checkpoint is updated **at every phase boundary**, not at close, and why that specific rule is what makes interruption free. Gives an example of a good checkpoint string and a useless one, and articulates the difference (does it let a cold session resume?). Explains what the parking lot is for and how items get there.

**Fails if:** checkpoint timing is described as "at the end of the session"; the candidate cannot produce a concrete good/bad example pair.

### C7 — The tutor's structural constraints, and their enforcement

**Observable:** States what the tutor is forbidden from doing — writing the candidate's code, grading, editing curriculum, overturning a verdict, pre-checking work informally — and names **which file** encodes each ban (`CLAUDE.md` for the constitution, the relevant `SKILL.md` for the protocol-level rules). Explains the escalation ladder's four rungs in order, that rung 4 is a *concept* walkthrough and never the active exercise's code, and that rung 4 is available on demand without penalty.

**Fails if:** rungs are given out of order or conflated; the candidate believes any rung produces their solution; a ban is stated without knowing where it lives.

### C8 — The refusal was demonstrated, and the escalation logged

**Observable:** The candidate asked the tutor outright to write their code during a rep and was **declined**. Repo evidence: `reps/` contains at least one exercise directory with a `README.md` and a runnable test file. Any rung ≥ 3 reached appears in `mastery.json.escalations` with `date`, `concept`, and `rung`.

**Fails if:** no rep directory exists; the tutor produced solution code and the candidate did not log it as a defect; a rung-3+ hint was given but never recorded.

---

## Also required to pass the gate

Beyond the eight criteria, the module gate requires the **portfolio write-up** — the write-up sits inside the gate, not after it. For Module 0 that is a short entry in `portfolio/index.md` claiming what you can now do, plus the **north-star declaration** in the journal (target user, core job, tool surface, data sources, one success metric).

A module does not advance on criteria alone. `gates.00-bootstrap.status` moves to `passed` when all eight criteria pass **and** both artifacts exist.

---

## Transfer question

Asked at every gate, unscored but recorded in the journal:

> **Same problem, different domain — what changes?** You have just described a system whose central design move is separating the agent that helps you from the agent that judges you. Name another domain where that separation is load-bearing, and say what would go wrong without it.
