---
module: 00-bootstrap
last_verified: 2026-07-29
---

# Module 0 — Bootstrap: the campus is the curriculum

You are about to spend months being taught by an agent system. Module 0's premise is that you should understand the machine before you trust it — and that dissecting it is the fastest possible introduction to agent architecture, because this agent is small enough to read in an afternoon and consequential enough that its design choices are real.

There is no framework here. No orchestration library, no database, no server. A handful of markdown files and two JSON files. That is deliberate, and by the end of this module you should be able to say why.

---

## 1. Anatomy of this tutor

### 1.1 Four agents, four jobs, one reason

| Agent | Owns | Writes to | Status in v0.1 |
|---|---|---|---|
| **Tutor** | the session (tactical) | student model, journal | **active** |
| **Grader** | verdicts, per artifact | mastery evidence, gate verdicts | **active** |
| **Examiner** | retention | review queue | staged, v0.2 |
| **Director** | the course itself (meta) | `curriculum/`, syllabus, rubrics | staged, v0.3 |

The load-bearing idea is **separation of powers**, and it exists to defeat one specific failure: an agent that likes you will tell you your work is good.

Three rules make this a system rather than role-play:

1. **The tutor cannot edit the curriculum.** So it cannot quietly lower the bar when you are frustrated.
2. **The tutor cannot overturn the grader.** It can explain a verdict, argue with it out loud, and build a remediation plan. It cannot change the outcome.
3. **Only the director changes the course**, and every change is a git commit with a rationale. Auditable, reversible, and immune to in-the-moment negotiation — because the director acts *between* sessions, not during frustration.

Notice what each rule really is: a **capability boundary**. Not a polite request in a prompt, but a structural constraint on who can write what. This is the single most transferable lesson in Module 0. When you design agents later, "I told it not to" is not a control. "It cannot" is.

### 1.2 Why the grader is a separate agent, not a separate instruction

The obvious cheaper design: one agent, told to "switch to grading mode and be strict." It fails, reliably, and the reason is worth internalising.

An agent holds the whole conversation in context. If it taught you the concept, watched you struggle, and saw you try hard for an hour, all of that is in its context window when it evaluates your work — and it will be weighed, whether or not you asked it to be. Effort contaminates judgement. Sympathy is a context leak.

The grader is spawned as a **subagent with a fresh context**. It receives paths — the rubric, the target, the hidden cases — and nothing else. `/grade` explicitly forbids the tutor from passing along how hard you tried or how close it came. The grader does not know you. That is the feature.

Second structural defence: **the grader executes.** It does not read your code and form an impression; it runs it, runs its tests, then runs hidden cases from `curriculum/modules/*/graders/` that you have not seen. Its prompt says a criterion you did not execute is a criterion you cannot pass.

Third: **all criteria pass → pass. Any criterion fails → fail.** No weighting, no rounding up, no "pass with notes." The arithmetic removes the negotiation.

### 1.3 The state files — where the system actually lives

Nothing important lives in the conversation. Everything lives in files.

```
student/
├── profile.md          who you are, goals, constraints (rarely changes)
├── mastery.json        the student model — what you know, proven
├── state.json          the in-flight session — crash-safe resume point
├── misconceptions.md   standing log of your recurring error patterns
└── journal/            one file per session date, appended as you go
```

**`mastery.json` — the student model.** Read it field by field; the Module 0 gate asks you to explain each one.

- `meta` — baseline, pace, and `current_module`. The last one is what every skill reads to know where you are.
- `concepts` — the core. One entry per kebab-case concept id (`async-python`, `tool-calling`), each with:
  - `mastery` — 0.0 to 1.0. Being *taught* a concept caps around 0.4–0.5. Higher is earned by unassisted reps and grader verdicts. This asymmetry is the whole philosophy in one number: listening is not knowing.
  - `last_touched`, `next_review` — the second is the examiner's field, unused until v0.2.
  - `evidence` — short factual strings citing a rep, a grade, or a review. Not opinions. `"rep-003 unassisted: passed 5/6, failed the empty-input case"` is evidence; `"doing well with async"` is not.
  - `misconceptions` — specific wrong models you have held.
- `gates` — per module: `locked` → `pending` → `passed`, plus the array of grader verdicts. A verdict is never deleted; a regrade appends with `regrade_of` pointing at the original. The history is the audit trail.
- `escalations` — every time you needed rung 3 or 4 of the hint ladder. Deliberately not shameful; it is the signal that tells the course where the curriculum is too steep.
- `mode_counts` — assisted versus unassisted work. The ratio the entire course exists to move.
- `streak` — freezes for declared breaks, never resets punitively.

**`state.json` — the crash-safe session.** Small, and the most operationally important file in the repo.

- `session.active` — if this is `true` at `/standup`, a session died mid-flight.
- `session.phase` — one of `review | teach | rep | build | grade | close`.
- `session.checkpoint` — **one human-readable sentence naming the exact resume point.** This is the file's reason for existing. `"teach: tool-calling, pass 2 of 3, just before the schema walkthrough"` lets a cold session resume precisely. `"working on module 1"` does not.
- `parking_lot` — threads deferred by the timebox, pre-loaded into the next session's plan so nothing silently drops.

The constitution requires the checkpoint to be updated **at every phase boundary**, not at session close. That is the difference between "quitting mid-session costs nothing" and "quitting mid-session loses an hour." Test it deliberately during this module's project — kill a session on purpose and see what survives.

### 1.4 Skills — the session verbs

Four, in v0.1: `/standup`, `/teach`, `/rep`, `/grade`. Each is a `SKILL.md` file under `.claude/skills/<name>/` containing a protocol the tutor follows step by step.

The design rule is **One Door**: you only ever need `/standup`. Everything else is discoverable through conversation and reachable by just saying what you want. Command sprawl is itself a UX failure mode — a course you need to memorise is a course you stop opening.

Read all four. They are short, and they are the operating manual for your own experience — including the parts that constrain what the tutor is allowed to do for you.

---

## 2. Claude Code internals, as used here

This section is about the runtime, because you are going to build on it.

### 2.1 `CLAUDE.md` — the constitution

`CLAUDE.md` at the repo root is loaded into context automatically at the start of every session. Here it holds the tutor's constitution verbatim: prime directives, teaching protocol, the escalation ladder, rep-mode rules, tone.

Two things to notice. First, it is **prose, not configuration** — the behavioural contract is written in the same language as the reasoning that follows it. Second, it is **short**. Every token in it is present in every single session, competing with actual work for context. A bloated CLAUDE.md is a real cost, paid continuously. Constitution-writing is an exercise in deletion.

### 2.2 Skills — progressive disclosure

A skill is a markdown file with YAML frontmatter (`name`, `description`) and a body. The critical mechanic: **only the description is loaded up front.** The body loads when the skill is actually invoked.

This is progressive disclosure, and it is why four detailed protocols cost almost nothing to have available. The `description` field is doing retrieval work — it must say not just what the skill does but *when to reach for it*, because that text is the only basis on which the runtime decides to load the rest.

### 2.3 Subagents — fresh context as a design tool

A subagent is defined by a markdown file in `.claude/agents/` with frontmatter (`name`, `description`, `model`, `effort`, and others) plus a system prompt. When spawned it gets its **own context window**, does its work, and returns a result to the parent.

Two distinct reasons to reach for one, and this course uses both:

1. **Isolation** — the grader must not see the teaching conversation. Fresh context *is* the guarantee.
2. **Economy** — a subagent's exploration doesn't pollute the parent's context, and each can run on a different model. The grader runs on the most capable model at high reasoning effort, because a wrong verdict is expensive. The examiner, when it activates, runs on the cheapest, because asking one recall question is not hard. Matching model cost to task difficulty is ordinary engineering, and you should do it deliberately.

**A trap worth knowing, because this repo hit it.** `.claude/agents/` is scanned **recursively** — putting a definition in a subdirectory does *not* deactivate it. And there is no `disabled` frontmatter key; an unrecognised key is silently ignored, which is the worst failure mode because it looks like it worked. So the staged examiner and director here are stored as `.md.staged`. Read `.claude/agents/_staged/README.txt` for the full account.

The general lesson: **verify what a mechanism actually does, rather than what its name implies.** A control you believe in but that isn't enforced is worse than no control, because you stop watching.

### 2.4 Context and compaction

The context window is finite. When a session runs long, the runtime **compacts** — summarising earlier turns to reclaim space. Detail is lost. This is not a bug to be avoided; it is a property to design around.

This system's answer: **all state lives in files, never in the conversation.** The constitution requires a silent re-read of the state files after any compaction or context loss. The session survives its own infrastructure.

That principle generalises hard. Any agent whose correctness depends on remembering something from 200 turns ago is an agent with a bug scheduled for later. If it matters, write it down.

---

## 3. Git discipline

Git is version control for everyone else. Here it is a second, richer memory — and a large fraction of your engineering credibility, because it is the part of your work a stranger reads first.

### 3.1 Commits as narrative

A commit is a unit of *meaning*, not a unit of time. The test: could someone reading only the log understand how the project got here and why?

- **One logical change per commit.** A bug fix and a refactor in one commit means neither can be reverted alone.
- **Subject line: imperative, ~50 characters, says what changed.** `add retry with backoff on 429` — not `updates`, not `wip`, not `fix stuff`.
- **The body explains *why*.** The diff already shows what. What it cannot show is the alternative you rejected and the reason. Six months later that is the only part you need.
- **`git log` is a document.** It should read like a change narrative.

This repo's own history is the worked example. Every commit here is `build(p<N>): <summary>` with a body explaining decisions and deviations. Run `git log` and read it — including the commit that documents the staging trap in §2.3.

### 3.2 When to commit

Commit when a thing works, or when a thing is a coherent step even if incomplete. Common failure modes at both ends:

- **Too rarely** — a 40-file commit that no one can review or revert, including you.
- **Too often, mechanically** — twelve `wip` commits that carry no information.

Working heuristic: commit when you would be annoyed to lose the work, or when you are about to try something risky and want a clean point to return to. Before a risky experiment, commit first — then you can be reckless cheaply.

### 3.3 What never goes in

Secrets. API keys, `.env` files, credentials, tokens. Git history is effectively permanent; a key committed and then deleted is still a leaked key and must be rotated. `.gitignore` exists for this and belongs in the repo from commit one — this one has `.env` in it already.

Also: nothing generated (`__pycache__/`, `node_modules/`, `.venv/`) and nothing enormous. The rule is source, not artifacts.

---

## 4. The rules of your own course

### 4.1 The escalation ladder

Pure Socratic tutoring is rage-inducing for adults. Answer-on-demand teaches nothing. The ladder is the compromise, climbed **one rung at a time**, only when you ask or are clearly stuck:

| Rung | What you get |
|---|---|
| 1 | A pointed question |
| 2 | A concept pointer — the idea's name, and where it is documented |
| 3 | A worked **analogous** example — different problem, same pattern |
| 4 | Full walkthrough of the concept |

Two hard boundaries. **Rung 4 is a walkthrough of the concept, never the code for your active rep or project** — there is no rung that produces your solution. And **you may demand rung 4 at any time**; it is granted immediately, without a lecture.

Rungs 3 and 4 are logged to `mastery.json.escalations`. Read that as instrumentation, not a rap sheet: a concept generating repeated rung-3s is a curriculum problem, and the log is what surfaces it.

The counterpart rule: after a concept fails three times, the tutor is **barred from explaining it the same way again**. It must switch analogy domain, decompose smaller, or build a micro-detour. Repeating the same explanation louder is the canonical bad-tutor failure, and here it is constitutionally illegal.

### 4.2 How grading actually runs

1. You invoke `/grade <path>`.
2. The tutor resolves the target and the module's `rubric.md`, then spawns the grader with paths only — no commentary, no context about your effort.
3. The grader reads the rubric, reads your code, then **runs it**: your tests, then hidden cases from `graders/`, then adversarial probes it generates itself — malformed inputs, wrong types, simulated dependency failures.
4. It returns a structured verdict: per-criterion `pass|fail` with **evidence** (what was run, what happened, the failing input or traceback), an `overall`, the single `highest_leverage_gap`, and the `model` id that produced it.
5. The verdict is appended to `mastery.json.gates.<module>.verdicts` and concept scores move — in either direction.
6. On a fail, the tutor builds a remediation plan sized to **one session** and schedules the regrade.

**Rubrics are public; test inputs are not.** You should know what good looks like — that is what a rubric is for. You should not be able to overfit to the specific cases, which is why `graders/` is off-limits. That split is standard practice for any serious eval, and you will rebuild it yourself in Module 3.

Failing is the system working. A gate everyone passes measured nothing.

### 4.3 Assisted and unassisted are both first-class

**Reps** are unassisted: autocomplete off, no AI pair, tutor hints only. **Builds** are assisted: full AI pair, because that is how the actual job works.

Neither is the virtuous one. The target is the sentence from Stripe's screen — *fluent with AI-assisted development but not dependent on it* — and both halves are real requirements. The ratio in `mode_counts` shifts toward unassisted early and back toward assisted later, on purpose.

If you paste AI-generated code into a rep, the tutor flags it once, neutrally, and logs the rep as assisted. No moralising, no second mention. The log exists so the ratio stays honest, not to catch you.

---

## 5. Why this system is as small as it is

The most counter-intuitive design decision here is everything that is **absent**. No database — two JSON files. No web UI — a terminal. No orchestration framework — markdown protocols. No spaced-repetition engine, no appeals process, no progress dashboard, though all three are designed and specified.

The rule is: **machinery earns its way in.** A mechanism ships only when its absence has produced a *logged* pain point — not a hypothetical one. The examiner activates the first time a review queue is genuinely non-empty. The director activates on the first disputed grade or skip request. Until then they sit in `_staged/`, visible and inert.

Corollary, and the sharpest rule in the constitution: **if a rule isn't enforced by a file or an agent, it doesn't exist.** Aspirational process is deleted on sight. Every rule in this course maps to something concrete — a capability boundary, a required file write, an arithmetic that removes discretion.

You will build agent systems after this course. The reflex to fight is reaching for the framework, the vector database, and the orchestration layer before you have a single logged instance of needing them. This repo is the counter-example: a course system that will run for a year, built out of files.

---

## Sources

Everything above is verifiable inside this repo — that is the point of the module.

- `CLAUDE.md` — the tutor's constitution
- `.claude/agents/grader.md` — the grader's adversarial prompt
- `.claude/agents/_staged/README.txt` — the staging trap, in full
- `.claude/skills/{standup,teach,rep,grade}/SKILL.md` — the session protocols
- `student/mastery.json`, `student/state.json` — the schemas described in §1.3
- `SPEC.md` §4 — the exact schemas, including the grader verdict shape
- `CONCEPT.md` — the design rationale, including the sources this pedagogy is stolen from
- `git log` — the build narrative, and the worked example for §3

For the runtime itself, read the current Claude Code documentation rather than trusting this file — subagent frontmatter keys in particular have changed and will change again. That instinct *is* the lesson of §2.3.
