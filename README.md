# The Tutor

A local-first AI-engineering course that lives in a git repo. A tutor agent teaches you, a separate adversarial grader agent judges your work, and a student model tracks what you actually know — not what you've been shown.

No database. No framework. No web UI. A handful of markdown files, two JSON files, and Claude Code as the runtime. That minimalism is a design position, not a shortcut, and the course explains why in Module 0.

---

## The core idea

> An agent that likes you will tell you your work is good.

Every "ChatGPT is my tutor" attempt dies of grade inflation, usually within two weeks. The model watches you struggle, holds that effort in its context, and starts rounding up. The feedback signal degrades smoothly enough that you don't notice the day it stopped being useful.

You cannot prompt your way out of this. `"Be strict"` and the contaminating context live in the same window, and context wins.

So the fix here is structural rather than aspirational:

- **The tutor teaches and never judges.** Grading happens only via `/grade`, which spawns a different agent.
- **The grader has a fresh context.** It receives file paths — the rubric, your code, hidden test cases — and nothing about how hard you tried. It runs your code rather than reading it. All criteria pass or the gate fails; no weighting, no "pass with notes."
- **The tutor cannot edit the curriculum.** So it can't quietly lower the bar on a bad day.
- **The tutor never writes your code.** Not in exercises, not in projects, not "just this once."

These are capability boundaries, not instructions. *"I told it not to"* is not a control. *"It cannot"* is.

## Getting started

```bash
git clone https://github.com/Sidgit11/AI-tutor.git
cd AI-tutor
claude
```

Then type:

```
/standup
```

That's the entire interface. One door.

It reads your state, proposes a plan sized to the time you actually have, and runs the session. `/standup 20` if you've got twenty minutes — a short session is a real session, and the system is built to never guilt-trip one. You never need to memorise the other commands; say "I want to practice" and it reaches for the right one.

Start at **Module 0**, whose project is *"read the system that is teaching you, and prove you understand it."*

## How a session works

```
/standup  →  reads state, proposes a plan, waits for your approval
             │
             ├── TEACH   three passes: intuition → mechanism → production failure modes
             │           one check question gates each advance
             ├── REP     unassisted. Hints only, via a four-rung escalation ladder.
             │           The tutor will not write your code, and you can't talk it into it.
             ├── BUILD   assisted. Full AI pair — that's how the job works too.
             └── GRADE   spawns the grader. Its verdict is binding.
             │
             └── CLOSE   journal written, student model updated, threads parked
```

State is checkpointed at **every phase boundary**, not at close. Quitting mid-session — meeting, kid, dead battery — costs nothing. The next `/standup` offers to resume from the exact point you left.

## Repo map

```
CLAUDE.md                       the tutor's constitution — loaded every session
.claude/
  agents/grader.md              the adversarial evaluator
  agents/_staged/               examiner (v0.2) and director (v0.3) — inert
  skills/{standup,teach,rep,grade}/
curriculum/
  syllabus.md                   nine modules, mastery-gated
  modules/00-bootstrap/         concepts · project · rubric
  modules/01-floor/             + graders/ (hidden test cases)
student/
  profile.md                    who you are, goals, baseline
  mastery.json                  the student model — concepts, gates, evidence
  state.json                    in-flight session, checkpoint, parking lot
  misconceptions.md             standing log of recurring error patterns
  journal/                      one file per session
reps/  projects/  portfolio/
```

## The student model

`mastery.json` is the spine. The design decision worth noticing: **being taught something caps its mastery around 0.4–0.5.** Higher is earned only by unassisted exercises and grader verdicts.

Evidence strings are factual, never evaluative:

```json
"evidence": [
  "taught 2026-07-29: pass 1 (intuition) and pass 2 (mechanism); pass 3 parked for timebox",
  "rep-003 unassisted: passed 5/6, failed the empty-input case, rung-2 hint on the generator"
]
```

`"doing well with async"` is not evidence. If it isn't in the model, it didn't happen.

## The curriculum

| # | Module | Artifact |
|---|---|---|
| 0 | Bootstrap | Operate the campus; explain its architecture cold |
| 1 | The floor | Deployed CRUD service with auth, tests, CI — **zero AI in it** |
| 2 | LLM mechanics | Structured-extraction service across two providers |
| 3 | Evals | An eval harness — *and a PR improving this course's own grader* |
| 4 | Retrieval | Hybrid retrieval over a messy corpus, measured |
| 5 | Agents | A useful agent + MCP server; rebuild the tutor loop in raw Python |
| 6 | Production | Cost/latency benchmark, tracing, injection defense |
| 7 | Open-weight stack | Frontier → open migration with measured deltas |
| 8 | Capstone | One system, end to end, for a real user |

Modules 0 and 1 are written. **2–8 are deliberately stubs** — at intake you declare a north-star product, and the curriculum compiles module projects against it, so you graduate holding a working product rather than eight disconnected exercises.

Module 1 is where the design shows its teeth: it forbids AI features entirely. You can already build AI features. What survives an unassisted screen is the floor underneath.

## Staged, not built

v0.1 ships the tutor and the grader. Two more agents are written, reviewed, and sitting inert in `.claude/agents/_staged/`:

- **Examiner** (v0.2) — spaced-repetition retention. Activates the first time a review queue is non-empty.
- **Director** (v0.3) — the only agent that can change the curriculum; owns appeals, skips, and pacing. Activates on the first disputed grade or skip request.

They are staged rather than shipped on principle: **machinery earns its way in.** A mechanism ships when its absence has produced a *logged* pain point, not a hypothetical one. The corollary is the sharpest rule in the system — if a rule isn't enforced by a file or an agent, it doesn't exist, and aspirational process is deleted on sight.

A note for anyone reading this to learn from it: `.claude/agents/` is scanned **recursively**, and `disabled:` is not a real frontmatter key. Neither a subdirectory nor that flag will deactivate an agent — which is why the staged prompts carry a `.staged` extension instead. `.claude/agents/_staged/README.txt` has the full account. Verify what a mechanism *does*, not what its name implies.

## Design sources

Bloom's 2-sigma problem (mastery tutoring works); Andrew Ng's autograder (objective feedback beats lectures); Math Academy (knowledge graph + spaced review); Khanmigo (Socratic by policy) tempered with an escalation ladder, because pure Socratic method is rage-inducing for adults; CS50's duck (banned from writing your solution); fast.ai (play the whole game first); Anki/FSRS; cognitive apprenticeship (modeling → scaffolding → *scheduled* fading).

`CONCEPT.md` has the full rationale. `SPEC.md` is the build contract this was built against.

---

Built with [Claude Code](https://claude.com/claude-code). Single-user by design — the interesting parts are the student-model schema, the rubric library with hidden case banks, and the grader-separation pattern.
