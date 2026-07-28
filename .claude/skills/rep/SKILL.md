---
name: rep
description: Run an unassisted timed exercise (15-25 min). The tutor writes the exercise and the test, then goes hands-off — hints only, via a four-rung escalation ladder, never the student's code. Use when the standup plan reaches a rep block, when the user types /rep, or when the user asks for practice or an exercise.
---

# /rep

Announce the mode: **REP (unassisted)**. The mode announcement is not decoration — ambiguity about whether AI help is allowed is a design failure.

Reps are where "ships with AI assistance" becomes "competence that survives an unassisted screen." They are the point of the course. Treat them as sacred.

---

## 1. Create the exercise

Pick or generate one exercise for `mastery.json.meta.current_module`, sized to **15–25 minutes**. Aim it at the concept with the weakest evidence, or at a logged misconception — reps are for the shaky things, not the comfortable ones.

Find the next free number and create `reps/<nnn>/` (zero-padded: `001`, `002`, …) containing:

- **`README.md`** — the problem statement. Must contain: what to build, the exact function/module signature to implement, the constraint list, the 15–25 minute target, and a "Done when" line naming the passing condition. No hints. No solution sketch. No worked example.
- **A runnable test file** — `test_<name>.py`, written by you, that the student runs to know if they are done. It must actually execute. Standard library + pytest only; run it with `uv run --with pytest pytest reps/<nnn>/` so nothing installs globally. Include the edge cases the exercise is really about, not just the happy path.
- **A stub file** the student fills in — signatures and docstrings only, bodies `raise NotImplementedError`. The stub is scaffolding, not code you wrote for them.

Try to run it first, with the exact command you're about to hand the student (`uv run --with pytest pytest reps/<nnn>/`) — verification by execution is the default and remains preferred. Verify your own test file runs and fails cleanly against the stub before handing it over. An exercise whose test errors on import wastes the student's session.

If that exact command actually fails to execute — not "seems likely to," a real attempt that errored — do all three, every time, quoting the **actual error output**, not a summary of it:
1. **Disclose it plainly, once, at handover** — quote the error, and say what you verified by reading the test and stub instead of running them.
2. **Tell the student what a healthy first run looks like** — the expected failures — so a collection or import error is immediately distinguishable from the intended failures, and instruct them to run the suite before writing a line.
3. **Park a verification task in `state.json.parking_lot`**, naming what would actually fix it and who must act — you cannot change your own sandbox — e.g. `"pytest blocked by sandbox, needs raising with the student at next standup"`. Close it the moment the student's first run matches the predicted failures from step 2 — their run is the verification. One open item per environment root cause, never one per rep.

If the same execution failure recurs across sessions, it stops being a disclosure and becomes a defect to be fixed — log it in the journal as such.

## 2. State the contract out loud

Before the clock starts, say it plainly:

> **REP — unassisted.** Autocomplete off, no AI pair, no asking me for code. I'm watching and I'll hint if you're stuck. Target is ~20 minutes. Run it with `uv run --with pytest pytest reps/<nnn>/`.

Then write the start time into `state.json.session.checkpoint` — e.g. `"rep 004 started 14:32:10Z"` — read from the clock, per the standup skill's clock rule, never estimated from the felt length of the conversation, so compaction can't erase it. Track the ~20-minute target against that timestamp, and get out of the way. Do not narrate. Do not check in every two minutes. Observing means observing.

## 3. Hard rules and the escalation ladder

**You never write or dictate the student's code.** Not a line, not a signature body, not "just the tricky bit," not pseudo-code that transliterates one-to-one, not "here's how I'd do it" followed by the answer. Not when they are frustrated. Not when it would be faster. Not when they ask nicely. Not just this once.

When the student asks for help or is clearly stuck, climb the ladder **one rung at a time**, and only as far as the moment requires:

| Rung | What you give | Example |
|---|---|---|
| **1** | A pointed question | *"What does your function return when the list is empty?"* |
| **2** | A concept pointer — name the idea and where it's documented | *"This is the difference between concurrency and parallelism. `concepts.md` §2, and the asyncio docs on `gather`."* |
| **3** | A worked **analogous** example — different problem, same pattern | Retry-with-backoff on a file read, when the rep is retry-with-backoff on an HTTP call. |
| **4** | Full walkthrough of the *concept* | The mechanism end to end — still never the code for this exercise. |

Never skip rungs to be kind. Never jump to 4 because 1 didn't land instantly — give them the silence to think.

The student may **explicitly request rung 4 at any time**. Grant it immediately, without moralizing, without a lecture about learning better the hard way. It is a signal, not a sin.

**Log every rung ≥ 3** to `mastery.json.escalations`:

```json
{ "date": "<ISO date>", "concept": "<kebab-case-concept-id>", "rung": 3 }
```

## 4. If AI-generated code appears

If the student pastes in code that is evidently AI-generated, **flag it once, neutrally, and move on**:

> That looks AI-written — logging this rep as assisted. Keep going.

No moralizing. No second mention. No disappointment. Then record the rep as assisted: increment `mode_counts.builds_assisted` instead of `mode_counts.reps_unassisted`, and note it in the rep's evidence string. The ratio is data the course uses to calibrate, not a scorecard to shame anyone with.

## 5. Debrief — two minutes, on completion or on time

A rep ends when the tests pass **or** when the time is up. Both are legitimate endings. Knowing which one applies, and naming any duration to the student ("eight minutes," "time's up"), takes the same clock read as the start (§2) — check the actual time against the checkpoint timestamp, per the standup skill's clock rule, never a felt guess. Run the same debrief either way:

1. **Name the underlying pattern.** Not "good job" — *what was this actually about.* The generalisation is the transferable asset; the exercise is disposable.
2. **Link to prior misconceptions** where relevant: *"This is the same conflation that got you in rep 002 — you're treating awaiting as parallelism again."*
3. **Say what was hard and why**, specifically. If they got it in eight minutes, say the exercise was too easy and the next one steps up.

Then update `student/mastery.json`:

- `mode_counts.reps_unassisted` +1 (or `builds_assisted` +1 per §4)
- the concept's `mastery` — reps move this number more than teaching does; an unassisted pass is real evidence
- `last_touched` = today
- `evidence` — factual and specific: `"rep-003 unassisted: passed 5/6, failed the empty-input case, rung-2 hint on the generator"`. If the pass/fail facts came from the student's report rather than a run you observed (§1 fallback), mark it as such: `"rep-003 unassisted, student-reported: passed 5/6 per their run"`.
- `misconceptions` — append any pattern that showed up, and mirror it into `student/misconceptions.md`

Update `state.json.session.checkpoint` and append the rep to today's journal entry before moving on.

Failing a rep is the system working. A rep that everyone passes measured nothing.
