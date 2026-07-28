---
module: 00-bootstrap
project: Operate your campus
---

# Module 0 Project — Operate your campus

Every other module ends in software you built. This one ends in **operational fluency with the system that will teach you for the next year**, demonstrated rather than claimed.

There is a reason it comes first beyond the obvious. You cannot evaluate a tutor you do not understand, and you should not outsource a year of your development to a machine whose rules you have not read. By the end of this project you will have read every file that governs your own course, and you will have deliberately broken and recovered the thing that keeps your progress safe.

**Zero code is written in this project.** The artifact is evidence, not a repo.

---

## Deliverables

Four tasks. Each produces a trace in the repo — a journal entry, a state file, an escalation log — that the oral defense will draw on. Do them in order; each depends on the last.

### Task 1 — Run a complete session loop

Run one full `/standup` session, start to finish, of any length ≥ 30 minutes.

**Done when:**
- `student/journal/<date>.md` exists and contains what was covered, any escalations, and a next-session seed
- `student/mastery.json` shows at least one concept touched, with an `evidence` string that is factual and specific
- `student/state.json` has `session.active: false` and a populated `last_closed`
- `streak.count` has incremented

**Watch for:** whether the tutor proposed a plan sized to the budget you gave it, and whether it landed the plane at ~90% rather than running over. If it didn't, that's a finding — put it in the journal. You are also evaluating this system.

### Task 2 — Interrupt a session and resume it

This is the important one. Do not simulate it politely; actually kill it.

1. Start a session with `/standup` and get into a teach segment.
2. Partway through — mid-concept, not at a clean boundary — **quit the session outright.** Close the terminal.
3. Before restarting, open `student/state.json` and read `session.checkpoint`. **Write down what it says.**
4. Restart and run `/standup`.

**Done when:**
- the tutor detects `session.active: true` and offers resume-or-restart rather than starting fresh
- the checkpoint it resumes from is the one you wrote down
- resuming actually continues from that point — it does not re-teach what the journal already records

**The real question:** was the checkpoint specific enough to resume cold? `"teach: tool-calling, pass 2 of 3, just before the schema walkthrough"` is. `"working on module 0"` is not. If you got the second kind, that is a defect in how the session was run — record it in the journal with the exact string you saw. Finding it is worth more than passing smoothly.

### Task 3 — Trigger a rung-1 hint, and probe the boundary

Run `/rep` and take the toy exercise the tutor generates.

Then, deliberately, do two things:

1. **Get genuinely stuck and ask for help.** Confirm you receive a *pointed question* — rung 1 — and not an answer. Then climb one rung at a time by asking again, and observe the shape of each: pointer, then analogous example.
2. **Ask the tutor outright to write the solution for you.** Ask plainly, then ask again more insistently.

**Done when:**
- you have received a rung-1 hint and can describe how it differed from being told
- the tutor **declined** to write your code, and offered the ladder instead
- any rung ≥ 3 you reached appears in `mastery.json.escalations` with date, concept, and rung

**Note what the refusal felt like.** If it moralised, lectured, or made the refusal feel like a judgement, that is a constitution defect worth logging — the rule is decline-without-moralising, and rung 4 on demand is granted without a lecture.

### Task 4 — Read every state file and explain it

Read, in full, with the actual files open:

- `student/mastery.json` — every field, including the ones currently empty or null
- `student/state.json` — every field, including `phase` and `parking_lot`
- `CLAUDE.md` — the whole constitution
- `.claude/skills/*/SKILL.md` — all four
- `.claude/agents/grader.md` — the prompt that will judge your work
- `.claude/agents/_staged/README.txt` — why two agents are inert

**Done when** you can, without looking:

- name every top-level key in `mastery.json` and say what it is for
- explain why `next_review` is currently `null` on every concept
- explain what makes a `checkpoint` string good or useless, with an example of each
- state what the tutor is structurally forbidden from doing, and which file forbids it
- explain why the grader is a separate agent rather than a mode of the tutor

You will be asked these cold. Reading them once is not enough; the gate is oral.

---

## Intake — the north star

At the **end** of this module, before the gate, you declare your **north-star product**: the agent you actually want to exist. Target user, the core job it does, its tool surface, its data sources, and one success metric.

Every subsequent module project then compiles against it — Module 1's CRUD service becomes *your product's* backend, Module 4's retrieval system runs over *your product's* corpus. You graduate holding a working product with eight graded milestones behind it, rather than eight disconnected exercises.

Intake is run by the **director**, which is staged for v0.3 and not yet active. So for v0.1: **write your north star into the journal at module close** — target user, core job, tool surface, data sources, one success metric. When the director activates, it compiles the curriculum from that entry. Do not skip it because the mechanism isn't built yet; the thinking is the point, and it is easier to do now than to retrofit.

---

## How this gets graded

By **oral defense**, not by the grader agent — there is no code to execute. See `rubric.md` for the criteria, which are observable and which you should read before you start.

Read the rubric first. You should always know what good looks like; that's what rubrics are for. What you don't get to see is `graders/` — hidden cases start in Module 1.
