---
name: standup
description: Opens, resumes, and closes a study session. Reads the student model, proposes a plan sized to the time budget, keeps state.json checkpointed at every phase boundary, lands the plane at 90% of budget, and writes the journal at close. Use whenever the user types /standup, says they're starting or resuming a session, or asks what to work on today.
---

# /standup [minutes]

The one door. Every session opens here. The student should never need to know any other command exists.

`minutes` is optional. `/standup` with no argument means 90.

---

## 1. Read state before saying anything

Read all three, silently, before your first line of output:

- `student/state.json`
- `student/mastery.json`
- the most recent file in `student/journal/` (highest date wins; if the directory is empty, this is session one)

Also read `student/profile.md` if you have not read it this session, and `student/misconceptions.md` if it has entries.

Never open a session from memory. If runtime compaction has occurred mid-session, re-read these files silently and continue — do not announce the re-read.

## 2. Check for an interrupted session

If `state.json.session.active` is `true`, a previous session ended abruptly. Do not start fresh by default. Show the checkpoint verbatim and offer exactly two options:

> Last session left off at: *"<state.json.session.checkpoint>"*
> Resume from there, or close it out and start fresh?

- **Resume** → keep `session.module`, set a new `planned_minutes` for today, continue from the checkpoint. Do not re-teach what the journal says was already covered.
- **Fresh** → close the old session properly first (§8 close sequence, journal entry noting it was interrupted), then proceed to §3.

v0.1 handles resume only. There is no comeback protocol — if the gap since `last_closed` is long, compute it with the same one-shot shell calculation as §6, not by feel, and note it in one neutral clause before moving on. If the clock is unavailable, say nothing about the gap at all rather than estimate it. No guilt language, no re-diagnostic ceremony.

## 3. Set the budget

`planned_minutes` = the number the student passed, else 90.

**Any budget ≥ 15 minutes is a legitimate session.** A 20-minute session that moves `mastery.json` is a win. Never suggest the student should have more time, never express disappointment at a short budget, never propose "we could go longer if you want." Size the plan to the budget you were given.

## 4. Propose the plan, then wait

Build a plan sized to the budget, in this priority order:

1. **Parking lot** — `state.json.parking_lot` entries come first. They were deferred from a previous session precisely so they would not be silently dropped.
2. **Current module work** — teach / build / rep for `mastery.json.meta.current_module`, informed by which concepts have low mastery, which gate is `pending`, and what the last journal entry named as the next-session seed.

Rough shapes, adapt to the actual budget:

| Budget | Shape |
|---|---|
| 15–30 min | one thing: a rep, or one teach pass, or a parking-lot item |
| 45–60 min | one teach segment + one rep, or one project milestone |
| 90 min | teach or build (45–60) + rep (15–25) + close (10) |

Present it as a short numbered list. **One line of rationale per item** — why this, now. Then stop and wait for approval or reshaping. The student may cut items, reorder, or substitute. Do not begin the first item until they respond.

Note: the `review` phase (spaced repetition, examiner agent) is **v0.2 and not active**. Do not schedule review blocks; do not claim concepts are "due."

## 5. Open the session

Once the plan is approved, write to `state.json`:

```
session.active         = true
session.started_at     = <ISO-8601 timestamp now, UTC, explicit Z or offset>
session.planned_minutes = <the budget>
session.module         = <mastery.json.meta.current_module>
session.phase          = <the first phase you are entering>
session.checkpoint     = "<one sentence: what is about to happen>"
```

`phase` must be one of: `review | teach | rep | build | grade | close`.

`started_at` — and every other timestamp written to any state file or journal, including `parking_lot[].added` and `last_closed` — is read from the system clock, never composed from memory or inferred from context, in the UTC ISO-8601 format above. Same rule as §6.

Then announce the mode and begin. Openings are two lines maximum.

## 6. Checkpoint discipline — load-bearing

**This is the single most important behaviour in this skill.** The system's crash-safety promise rests entirely on it.

At **every phase boundary** — and at every meaningful sub-boundary inside a long phase — update `state.json.session.checkpoint` to a one-sentence, human-readable resume point, and update `session.phase` if it changed.

A good checkpoint names the concept, the position within it, and what comes next:

> `"teach: tool-calling, pass 2 of 3, just before the schema walkthrough"`
> `"rep 003: student has the test failing on the retry case, no hints given yet"`
> `"build: M1 schema done, about to start the auth route"`

A bad checkpoint is `"working on module 1"` — it does not let a cold session resume.

**Append to the journal as you go, not only at close.** Open `student/journal/<YYYY-MM-DD>.md` at the first phase boundary and append to it throughout. If the runtime dies mid-session, everything up to the last boundary must already be on disk.

### The clock is not a feeling

You have no internal sense of elapsed time — you cannot feel a session getting long. Never read the clock and then subtract in your head: run **one shell command** that does both — reads the real system clock and parses `state.json.session.started_at` against it (e.g. a `python3 -c` that diffs the two ISO timestamps and prints minutes) — and state only the number that command printed. All timestamps you write anywhere — `started_at`, `last_closed`, `parking_lot[].added`, journal dates — are UTC ISO-8601 with an explicit offset or `Z`, so the subtraction is never a timezone guess.

Take this reading at every phase boundary, and — once elapsed exceeds 50% of `planned_minutes` — again at the top of every turn, so a single long phase (a 60-minute teach block, say) can't sail past the landing point unread. At most one clock read per turn, never more. Take it once more before any statement to the student about time.

**Never state, imply, or reason from an elapsed-time figure — or characterization ("we've been at this a while," "this is running long") — that was not derived from the clock this way.** An estimated minute count is a fabrication, not an approximation, and so is a vague characterization used to argue for a course of action.

Stating a wrong elapsed time to a student is worse than not mentioning time at all — especially when it is used to argue for a course of action. That is manufactured pressure built on a false fact. If the clock cannot be read, say time is unknown and proceed without a time-based argument. Do not guess.

## 7. Timebox — land the plane at 90%

At the first turn at or after 90% of `planned_minutes` (81 minutes into a 90-minute session; 27 into a 30) — computed from the clock read per §6, never estimated. You only get a turn when the student speaks, so this is the first opportunity to act on the mark, not the exact instant it passes. Stop starting new work and begin closing. Say so plainly:

> We're at the 90% mark — landing the plane.

Every unfinished thread goes to `state.json.parking_lot` as:

```json
{ "item": "<one sentence, specific enough to resume cold>", "added": "<ISO timestamp>" }
```

Sessions do not sprawl. Threads do not silently drop. If the student explicitly asks to continue past the timebox, that is their call — grant it without argument, and reset the landing point.

## 8. Close the session

**Closing is never the first thing the student hears of it.** Before beginning the sequence below, announce that you're landing and name what remains unfinished, **then stop and wait for the student's response** — same discipline as §4's plan approval — before running step 1. The one exception: an unprompted, explicit stop from the student ("I'm done," "gotta go") ends the *conversation* immediately, no negotiation, no landing announcement required — but the sequence below still runs in full. Assent to a wrap-up you proposed is not the student calling it; the announce-and-wait rule still applies to that case. A close that lands far short of the planned budget must say so plainly and record the actual elapsed time (clock-derived, per §6/§7) rather than the planned figure.

Run this sequence in order. All of it, every time.

1. **Journal.** Finalise `student/journal/<YYYY-MM-DD>.md`:
   - what was covered (concepts, reps, milestones)
   - escalations that occurred, with rung
   - anything the grader returned
   - **next-session seed** — one line naming where to pick up
2. **Mastery.** Update every concept touched in `mastery.json`: `mastery` score, `last_touched` = today, `evidence` entries (short, factual — `"taught: pass 1-3, check questions passed"`, `"rep-003: passed 4/5, failed the timeout case"`). Add any new `misconceptions`, and mirror recurring patterns into `student/misconceptions.md`. Increment `mode_counts` where applicable. Leave `next_review` alone — that is the examiner's field, v0.2.
   - **The shapes of `student/mastery.json` and `student/state.json` are fixed by SPEC section 4.** You may write values into the keys that schema defines; you may never add a key it does not define, at any nesting level, for any reason — not to preserve context, not to annotate, not "temporarily."
   - If something needs recording that the schema has no place for, it goes in the journal, which is free-form and exists precisely for that.
   - Before writing either file, confirm the key you are setting already exists in the schema.
3. **State.** `session.active = false`, `last_closed = <ISO now>`, `session.checkpoint` = a closing summary line. Keep the parking lot.
4. **Streak.** `streak.count` +1 if this session covered real work. `streak.frozen` is set only when the student declares a break. Streaks never reset punitively. An explicit student request to clear a streak is honoured — that is not punitive — but the prior value and the reason belong in the journal, not in a new field.
5. **Report** in three lines maximum: what moved, what's parked, what's next.

If the student vanishes mid-session, steps 1–3 have already been happening incrementally per §6 — that is the whole point.
