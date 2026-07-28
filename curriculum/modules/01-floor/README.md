# Module 1 — The floor

Backend Python without any AI in it. A deployed CRUD service with auth, tests, CI, and error handling that survives contact with reality.

| File | What it is | Who reads it |
|---|---|---|
| `concepts.md` | The source-of-truth notes the tutor teaches from and cites | **You**, freely |
| `project.md` | The project spec and its three milestones | **You**, freely |
| `rubric.md` | The ten observable criteria the gate is decided on | **You**, freely — read it *before* you build |
| `graders/` | Hidden adversarial scenarios the grader executes | **The grader only** |

---

## The `graders/` directory is off-limits

**You agree not to open `curriculum/modules/01-floor/graders/`.**

There is no technical enforcement. There is no permission bit, no encryption, no agent watching. It is an honour agreement, and it is worth being explicit about why it exists rather than treating it as arbitrary.

**Rubrics are public; test inputs are not.** You should know exactly what good looks like — that is what `rubric.md` is for, and you should read it before writing a line. What you should not have is the specific list of inputs your work will be run against, because a service built to pass a known list is a different artifact from a service that is actually robust. The first one passes the gate and fails in production. The second is the one you want.

This split is not a schoolteacher's trick — it is standard practice in any serious evaluation, and it is the same reason a held-out test set exists in machine learning. You will build exactly this public-rubric / hidden-case structure yourself in **Module 3**, and in Module 3 you also open this course's own grader and improve it. At that point the directory stops being off-limits, because by then you'll have earned the right to look at it the way an author does rather than the way a student does.

**If you open it by accident**, say so in the journal and tell the tutor. The honest cost is that the grader generates fresh cases for that criterion instead — a small inconvenience. The dishonest cost is that every subsequent verdict becomes information about nothing, including the ones you were proud of. The gate is only worth passing if it could have failed.

---

## Where to start

1. Read `concepts.md` — particularly §1 (concurrency vs parallelism) and §9 (debugging without AI), which are the two things this module is really for.
2. Read `rubric.md` in full. Know the standard before you build to it.
3. Read `project.md` and pick your domain.
4. `/standup` and let the tutor plan the first session.

The reps that run alongside this project are **unassisted**. The project itself is assisted — full AI pair, no AI *features*. Keep the distinction clear; the tutor announces the mode at every switch for exactly that reason.
