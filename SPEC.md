# SPEC — AI Engineer Course: The Tutor (v0.1 build contract)

This is the **build contract**. Build exactly what this file specifies — nothing more. `CONCEPT.md` (if present) is background reading only; where it and this spec differ, **this spec wins**.

---

## 0. Communication protocol (first-class requirement, not a courtesy)

The builder (you, Claude Code) must work in **phases with explicit check-ins**:

1. **Before writing anything:** present the phase plan with a file manifest (every file you intend to create, one line each) and wait for the user's approval.
2. **After each phase:** report — what was built, every decision you made that the spec left open, and any deviation you *propose* (never silently deviate; deviations require approval before implementation).
3. **On any ambiguity:** ask. Do not invent. A one-line question beats a plausible guess.
4. **One git commit per phase**, message format: `build(p<N>): <summary>`.
5. **At the end:** run the acceptance checklist (§9) *interactively with the user* — demonstrate each item live, don't just claim it.

Build phases: **P1** skeleton + schemas → **P2** agent prompts installed + skills → **P3** curriculum content → **P4** seed data + git remote + acceptance run.

---

## 1. Scope: build v0.1 ONLY

| Stage | Contents | Build trigger |
|---|---|---|
| **v0.1 — NOW** | Tutor + Grader agents; skills `standup` `teach` `rep` `grade`; `mastery.json` + `state.json`; Module 0–1 content; git repo | This build |
| v0.2 — LATER | Examiner agent; spaced review in standup; `/map` | First time the review queue is non-empty |
| v0.3 — LATER | Director agent; `/challenge` `/appeal`; comeback protocol; `CHANGELOG.md`; canary regrades | First disputed grade, skip request, or long usage gap |
| Intake — LATER | `northstar.md` + curriculum compilation | End of Module 0 |

Hard rules: **do not** build v0.2/v0.3 mechanisms, add dependencies beyond the standard library + pytest, introduce databases, frameworks, or a web UI. Plain files only. `prompts/examiner.md` and `prompts/director.md` exist in this kit for the user's review — **copy them into `.claude/agents/` but mark them `disabled: true` in frontmatter** (or place under `.claude/agents/_staged/`) so they are visibly staged, not active.

---

## 2. Final repo tree (v0.1)

```
ai-engineer-course/
├── CLAUDE.md                      # ← contents of prompts/tutor.md, verbatim
├── CONCEPT.md                     # background (copy if provided)
├── SPEC.md                        # this file
├── prompts/                       # source-of-truth agent prompts (user-reviewed)
├── .claude/
│   ├── skills/
│   │   ├── standup/SKILL.md
│   │   ├── teach/SKILL.md
│   │   ├── rep/SKILL.md
│   │   └── grade/SKILL.md
│   └── agents/
│       ├── grader.md              # ← prompts/grader.md + frontmatter
│       └── _staged/               # examiner.md, director.md (inactive)
├── curriculum/
│   ├── syllabus.md
│   └── modules/
│       ├── 00-bootstrap/          # concepts.md, project.md, rubric.md
│       └── 01-floor/              # concepts.md, project.md, rubric.md, graders/
├── student/
│   ├── profile.md
│   ├── mastery.json
│   ├── state.json
│   ├── misconceptions.md          # starts empty with header
│   └── journal/                   # empty dir with .gitkeep
├── reps/                          # rep exercises land here, one dir per rep
├── projects/                      # student project repos-in-repo
└── portfolio/
    └── index.md                   # empty table with header row
```

---

## 3. Agent prompts and models

Copy prompt files **verbatim** — do not rewrite, "improve," or summarize them. Add only frontmatter:

| Agent | File → destination | Frontmatter |
|---|---|---|
| Tutor | `prompts/tutor.md` → `CLAUDE.md` | none (session default model) |
| Grader | `prompts/grader.md` → `.claude/agents/grader.md` | `name: grader`, `description: Adversarial evaluator. Invoked only by /grade.`, `model: opus`, high reasoning effort if supported |
| Examiner | `prompts/examiner.md` → `.claude/agents/_staged/` | `model: haiku` (staged, inactive) |
| Director | `prompts/director.md` → `.claude/agents/_staged/` | `model: opus` (staged, inactive) |

---

## 4. Schemas (exact)

### `student/mastery.json`
```json
{
  "meta": {
    "created": "<ISO date>",
    "baseline": "ships-with-ai-assistance",
    "pace_hours_per_week": "5-10",
    "current_module": "00-bootstrap"
  },
  "concepts": {
    "<concept-id>": {
      "mastery": 0.0,
      "last_touched": null,
      "next_review": null,
      "evidence": [],
      "misconceptions": []
    }
  },
  "gates": {
    "00-bootstrap": { "status": "pending", "verdicts": [] },
    "01-floor":     { "status": "locked",  "verdicts": [] }
  },
  "escalations": [],
  "mode_counts": { "reps_unassisted": 0, "builds_assisted": 0 },
  "streak": { "count": 0, "frozen": false, "last_session": null }
}
```
Concept IDs are kebab-case (`async-python`, `tool-calling`). Mastery is 0.0–1.0. `evidence` entries are short strings citing a rep, grade, or review result.

### `student/state.json`
```json
{
  "session": {
    "active": false,
    "started_at": null,
    "planned_minutes": null,
    "module": null,
    "phase": null,
    "checkpoint": null
  },
  "parking_lot": [],
  "last_closed": null
}
```
`phase` ∈ `review | teach | rep | build | grade | close`. `checkpoint` is a one-sentence human-readable resume point (e.g., `"teach: tool-calling, pass 2 of 3, just before schema walkthrough"`). `parking_lot` entries: `{ "item": "...", "added": "<ISO>" }`.

### Grader verdict (appended to `gates.<module>.verdicts` and echoed to the user)
```json
{
  "rubric": "01-floor-gate",
  "graded_at": "<ISO>",
  "model": "<model id as reported by the runtime>",
  "criteria": [ { "id": "c1", "verdict": "pass|fail", "evidence": "<what was run, what happened>" } ],
  "overall": "pass|fail",
  "highest_leverage_gap": "<one sentence, empty if pass>",
  "regrade_of": null
}
```

---

## 5. Skill protocols

Write each as a `SKILL.md` implementing exactly these steps. Skills are instructions to the tutor (main session), except `grade`, which spawns the grader agent.

### `/standup [minutes]`
1. Read `state.json`, `mastery.json`, latest `journal/*.md`.
2. If `session.active` is true → an interrupted session exists. Offer: **resume from checkpoint** or close it and start fresh. (v0.1 handles resume only; no comeback protocol.)
3. Default `planned_minutes` = 90 unless the user passed a number. Any number ≥ 15 is a legitimate session — never guilt-trip short sessions.
4. Propose a plan sized to the budget: parking-lot items first, then teach/build/rep for the current module. One-line rationale each. Wait for approval or reshaping.
5. Set `session.active = true`, write `started_at`, `planned_minutes`, `module`.
6. **Checkpoint discipline (load-bearing):** update `state.json.checkpoint` at every phase boundary and journal-append as you go — never only at close.
7. **Timebox:** at ~90% of budget, land the plane — unfinished threads go to `parking_lot`, then close.
8. Close: write journal entry (what was covered, escalations, next-session seed), update `mastery.json` touched concepts, set `session.active = false`, `last_closed = now`, streak +1.

### `/teach` (invoked from the plan; also usable directly)
1. Teach the planned concept in **three passes**: intuition (why it exists) → mechanism (how it works) → production failure modes (how it breaks).
2. Before advancing each pass, ask one check question and wait for the answer. Wrong answer → address the gap now; log a misconception if it's a pattern.
3. Teach from `curriculum/modules/<current>/concepts.md`; cite it. For anything vendor- or version-current, search the web rather than answering from memory.
4. Never re-deliver an explanation that already exists in the journal — reference and extend.
5. On completion, update the concept in `mastery.json` (evidence: `"taught: pass 1-3, check questions passed"`).

### `/rep`
1. Pick or generate an exercise for the current module (15–25 min), write it to `reps/<nnn>/` with a `README.md` and a runnable test file.
2. State the contract: **unassisted** — autocomplete off, no AI pair. You (tutor) give hints only.
3. **Hard rules:** never write or dictate the student's code. Escalation ladder, one rung at a time, only when asked or clearly stuck: (1) pointed question → (2) concept pointer → (3) worked *analogous* example (different problem) → (4) concept walkthrough — still never the exercise's code. Log every rung ≥ 3 to `mastery.json.escalations`.
4. If the student pastes in AI-generated code, flag it once, without moralizing, and note the rep as assisted.
5. On completion (tests pass or time up): 2-minute debrief — name the underlying pattern, link to any prior misconception, update `mastery.json` (`mode_counts.reps_unassisted` +1).

### `/grade <path>`
1. Confirm target (a rep dir or `projects/<name>`), then spawn the **grader agent** with: the rubric file for the current module/milestone, the target path, and write access to `mastery.json`.
2. The tutor (you) does **not** grade, pre-review, or soften. After the verdict returns: you may discuss it, explain it, and build a remediation plan — you may never overturn it or promise a different outcome.
3. On fail: propose a remediation plan sized ≤ 1 session, schedule the regrade.

---

## 6. Curriculum content to author (P3)

### `curriculum/syllabus.md`
The 9-module table (0–8) from CONCEPT.md §6, with the note that modules 2+ are stubs pending intake compilation. No calendar durations — modules are gated by mastery, not time.

### `modules/00-bootstrap/`
- `concepts.md` — written for a founder-PM who ships with AI assistance: (1) anatomy of this tutor (agents, skills, state files — teach the system itself), (2) Claude Code internals as used here (CLAUDE.md, skills, subagents, context & compaction), (3) git discipline (commits as narrative, when to commit), (4) how the escalation ladder and grader work — the student should know the rules of their own course. Mark a `last_verified: <date>` header.
- `project.md` — "operate your campus": run a full session loop, interrupt and resume a session, trigger a rung-1 hint in a toy rep, read every state file and explain each field.
- `rubric.md` — gate: **oral defense**: explain the tutor's architecture cold (agents, state flow, why grader is separate); demonstrate a resume-from-checkpoint; explain what `mastery.json` fields mean. Criteria must be observable.

### `modules/01-floor/`
- `concepts.md` — backend Python floor: async/await & concurrency vs parallelism, typing, pytest, FastAPI basics, Postgres + schema design, Docker, CI with GitHub Actions, structured logging, debugging *without* AI. Cite primary docs. `last_verified` header.
- `project.md` — deployed CRUD service with auth, tests, CI, real error handling. **Zero AI features.** Milestones: M1 schema+API local, M2 tests+CI green, M3 deployed+documented.
- `rubric.md` — observable criteria, e.g.: malformed request returns 4xx with a structured error (not a stack trace); DB down → service degrades with a clear error, doesn't crash; tests cover the auth boundary; CI fails on a seeded bug.
- `graders/` — 8–10 hidden test scenarios the grader executes (malformed payloads, auth bypass attempts, connection-kill mid-request). Student agrees not to open this directory; note that in the module README.

---

## 7. Seed data (P4)

- `student/profile.md`: name Siddhant; 0→1 product manager / founder (AI SaaS — trade intelligence); baseline: ships with AI assistance — can build working systems with AI pair, target is competence that survives unassisted screens; pace 5–10 hrs/week in 60–90 min blocks; target roles: Applied/Product AI Engineer, Forward-Deployed Engineer; north star: *to be declared at intake (end of Module 0)*.
- `mastery.json`: schema-valid, concepts empty, gates as in §4, `meta.created` = build date.
- `portfolio/index.md`: header table (Artifact | Module | Date | Link | One-line claim), no rows.

---

## 8. Git (P4)

`git init`, default branch `main`, commit per phase (§0). Add remote and push **only after asking the user for the remote URL** (they will create a private GitHub repo). `.gitignore`: `__pycache__/`, `.env`, `.venv/`, `node_modules/`, `.DS_Store`.

---

## 9. Acceptance checklist (run interactively with the user, final phase)

1. `/standup 30` → reads state, proposes a plan sized to 30 minutes.
2. Start a teach segment, then simulate an interruption (user quits). Restart → `/standup` offers resume from the exact checkpoint.
3. `/rep` → timed exercise created in `reps/001/`; ask the tutor outright for the solution → it declines per constitution and offers rung 1.
4. `/grade` on a deliberately broken toy submission (builder prepares one) → per-criterion verdict with evidence, `overall: fail`, `highest_leverage_gap` present, model id recorded, `mastery.json` updated.
5. Close the session → journal entry exists, mastery updated, `session.active` false; a second `/standup` reflects all of it.
6. Ask the tutor to "make the Module 1 gate easier" → it declines: curriculum changes are the director's power, and the director isn't active yet.

Every item demonstrated live. Then final commit and push.
