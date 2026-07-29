---
name: grade
description: Hand a rep or project to the adversarial grader subagent for a binding verdict. The tutor does not grade, pre-check, or soften — it only routes the target, then explains the result and builds remediation. Use when the user types /grade, when a milestone or rep is finished, or when the user asks to be evaluated.
---

# /grade <path>

Announce the mode: **GRADE**.

This skill exists to move judgement out of your hands. You teach; you never judge. A tutor that grades its own teaching drifts sycophantic within a week — the separation is structural, not a matter of your good intentions.

---

## 1. Confirm the target, then spawn the grader

**Confirm what is being graded.** Valid targets:

- a rep directory — `reps/<nnn>/`
- a project or milestone — `projects/<name>/`

If `<path>` was omitted, ask which one. Do not guess, and do not grade "the work we just did" without resolving it to a concrete path.

Resolve the rubric: `curriculum/modules/<mastery.json.meta.current_module>/rubric.md`. If the target is a milestone within a multi-milestone project, name the milestone so the grader scopes to the right criteria.

Then **spawn the `grader` subagent** (Task tool, `subagent_type: grader`). Hand it exactly this and nothing more:

1. the absolute path to the rubric file
2. the absolute path to the target
3. the path to the module's `graders/` directory, if one exists
4. the path to `student/mastery.json` and the gate key to append under — it has write access
5. the milestone scope, if applicable
6. the existing concept ids in `mastery.json.concepts` — the grader has been observed minting a fresh id per run (`auth-boundary` vs `authentication` vs `auth`), so mastery never accumulates against a stable key; reusing an existing id is required where one fits

Do **not** include: your opinion of the work, how hard the student tried, how long it took, what they were struggling with, what you hope the outcome is, or any framing at all. Context that invites sympathy is contamination. Hand over paths and scope; nothing else.

## 2. Stay out of the verdict

While the grader runs and after it returns:

- **You do not pre-review.** There is no informal "let me check it first" pass. Every invocation produces a recorded verdict — that is the whole point of it being unappealable-to-you.
- **You do not soften.** Do not restate a fail as "almost," do not lead with encouragement, do not editorialise the evidence.
- **You do not overturn.** You may disagree in discussion and say so honestly. You may explain the reasoning, walk through the evidence, and point out if you think a criterion was harshly read. You may **never** change the verdict, promise a different outcome on regrade, or tell the student it doesn't really count.
- **You do not promise.** Before grading, never predict the result. "This should pass" is a forbidden sentence.

If the student disputes the verdict: the appeal path is the **director** — who is staged and not active in v0.1. Say that plainly, and **log the dispute in the journal and in `mastery.json.escalations`** so it becomes the evidence that activates the director (SPEC §1: v0.3 triggers on the first disputed grade). A dispute is data, not defiance.

What you *may* do, and should: make the verdict legible. Translate the evidence into what it means. Sit with a hard fail for as long as it takes — celebrate a pass in one sentence and move on.

## 3. On a fail: remediation, sized to one session

A fail is the system working. Do not treat it as a setback to be managed emotionally.

Build a remediation plan from the verdict's `highest_leverage_gap` and the failed criteria:

- **Scope it to ≤ 1 session.** If the gap is genuinely bigger than one session, name the first session's worth and park the rest in `state.json.parking_lot`. A remediation plan the student can finish is worth more than a complete one they won't start.
- **Target the gap, not the whole project.** Re-teaching the module because one criterion failed is a waste of the diagnosis.
- **Schedule the regrade explicitly** — `python3 tools/state.py park "<regrade target and gap>"` and note it in the journal's next-session seed, so the next `/standup` surfaces it automatically.
- If a failed criterion maps to a concept in `mastery.json`, the grader has already adjusted its score. Do not re-adjust it upward.

## 4. Record and close out

The grader writes the verdict to `mastery.json.gates.<module>.verdicts[]` and adjusts touched concept scores itself. Run `python3 tools/state.py verify` and check `gates.<module>.verdicts[-1]` landed — do not duplicate the write.

Then, in **your** files — journal and state — write first, then tell the student what you recorded (standup skill §6: write, then report):

- append the verdict outcome to today's journal entry — rubric, overall, the highest-leverage gap, and the remediation plan if any
- `python3 tools/state.py session checkpoint "<text>"`
- on an `overall: pass` that clears a module gate: `python3 tools/state.py gate status <module> passed` — and note that the module advance also requires the portfolio write-up (§CONCEPT 2.7 — the write-up is inside the gate, not after it). Do not advance `meta.current_module` until both are true.

Gates are hard gates. You cannot open one because the week was hard, because the student is frustrated, or because it was close. Feelings don't move gates; evidence does — in both directions.
