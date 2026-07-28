---
module: 01-floor
rubric: 01-floor-gate
gate_type: executed against the deployed service and the repo
---

# Module 1 Gate — Rubric

**Executed, not read.** Every criterion below is decided by running something and observing what happens. The grader runs your test suite, then runs hidden scenarios from `graders/`, then generates fresh adversarial cases of its own. Evidence for each criterion must name what was run and what happened — the request sent, the status returned, the traceback if any.

**Scoring: `pass` or `fail` per criterion. All ten pass → gate pass. Any one fails → gate fail.** No weighting, no partial credit, no "pass with notes." A criterion the grader could not execute is a criterion that cannot pass.

Criteria are scoped by milestone so partial submissions can be graded: **M1** → C1–C4, **M2** → C5–C7, **M3** → C8–C10. A full gate pass requires all ten.

---

## M1 — Schema and API

### C1 — A malformed request returns a structured 4xx, not a stack trace

**How it's tested:** Requests with wrong field types, missing required fields, `null` where a value is required, absurd values (negative where positive is required, a 10MB string in a name field), malformed JSON, and wrong content-type.

**Passes when:** every one returns a 4xx with a consistent, machine-readable body identifying what was wrong. The envelope shape is the same across all of them.

**Fails when:** any produces a 500, a stack trace, framework HTML, an empty body, or a raw driver error. Also fails when malformed input returns a *200*.

### C2 — Database down: degrades with a clear error, does not crash

**How it's tested:** The database is stopped and requests are sent. Then a connection is killed **mid-request**. Then the database is restored and normal requests are sent again.

**Passes when:** the service stays up throughout; requests return a clear 5xx within a bounded time; the health check reports unhealthy while the DB is gone; and the service **recovers on its own** once the DB returns, without a restart.

**Fails when:** the process dies, requests hang indefinitely (no connection timeout), a driver traceback reaches the client, or the service does not recover without manual intervention.

### C3 — Authorization is enforced, not just authentication

**How it's tested:** A valid credential for user A is used against user B's resources — read, update, and delete. Also: no credential, a malformed token, a tampered token, an expired token, and a token from a deleted user. Resource ids are enumerated to check for direct-object-reference holes.

**Passes when:** every cross-user access returns 403 or 404 (consistently — either is defensible, but pick one), and every invalid-credential case returns 401. No data from another user leaks in any response body, including error messages.

**Fails when:** any cross-user access succeeds; a tampered or expired token is accepted; error responses disclose whether another user's resource exists when it shouldn't.

### C4 — Schema and response models are sound

**How it's tested:** Migrations run against an empty database. The DDL is inspected. Response bodies are examined for leaked fields.

**Passes when:** migrations build the schema from empty; there are ≥ 2 related tables with a real foreign key with deliberate `ON DELETE` behaviour; constraints exist at the database level (`NOT NULL`, `UNIQUE`, FKs); timestamps are `timestamptz`; **no password hash or secret appears in any response body**; list endpoints paginate.

**Fails when:** the schema can only be created by hand; constraints exist only in application code; a naive `timestamp` is used for real times; any endpoint returns a credential field; a list endpoint returns unbounded rows.

---

## M2 — Tests and CI

### C5 — Tests cover the auth boundary

**How it's tested:** The test suite is read and executed. The grader checks for tests exercising: no credential, malformed credential, expired credential, and **a valid credential against another user's resource**.

**Passes when:** all four exist as real tests and pass, and they run against a **real Postgres**, not a mock.

**Fails when:** any of the four is missing; auth tests only cover the happy path; the suite mocks the database (a mocked DB does not test your schema, which is where the bugs are). Coverage percentage is not evidence for this criterion.

### C6 — CI fails on a seeded bug

**How it's tested:** The grader introduces a defect into the codebase — a broken validation rule, an auth check inverted, or a schema constraint removed — and runs the pipeline.

**Passes when:** the pipeline goes red, and the failure output identifies what broke.

**Fails when:** the pipeline stays green, fails for an unrelated reason (a flaky step, a missing secret), or the test step is configured not to fail the build. A pipeline that cannot go red is worse than no pipeline, because it is trusted.

### C7 — The pipeline is real and current

**How it's tested:** The workflow file is inspected and the pipeline is run.

**Passes when:** it checks out, installs, lints, type-checks, and runs tests against a Postgres service container, on push; and it uses currently supported action versions and runtimes (see `concepts.md` §7 — as of 2026-07-29: `actions/checkout` v7, `actions/setup-python` v7 with the `pip-install` input removed, `ubuntu-latest` = 24.04, and nothing pinned to the Node 20 action runtime removed 2026-09-16).

**Fails when:** type checking or linting is absent; tests run against a mock or SQLite instead of Postgres; the workflow depends on a removed runtime or a removed action input.

---

## M3 — Deployed and documented

### C8 — Deployed, reachable, and honestly health-checked

**How it's tested:** The public URL is hit cold. The health endpoint is checked while healthy, then while the database is unreachable.

**Passes when:** the deployed service responds; the health check returns healthy when it is and **unhealthy when the database is gone**.

**Fails when:** the URL is unreachable; the health check returns 200 unconditionally (a health check that cannot fail reports nothing).

### C9 — The container is production-shaped

**How it's tested:** The image is built and inspected. The image and repo are scanned for credentials.

**Passes when:** it is a multi-stage build; the process runs as a **non-root** user; **no secrets are baked into the image or committed to the repo**; config comes from the environment; `.env` is gitignored.

**Fails when:** the container runs as root; any credential, token, or key appears in the image layers, the repo, or git history. *(A secret found in history is a fail even if deleted from the working tree — and it must be treated as leaked and rotated.)*

### C10 — Documentation lets a stranger run it, and logs are usable

**How it's tested:** The grader follows the README from a clean checkout with no other information, and inspects log output during the scenarios above.

**Passes when:** the README covers what it does, local setup, running the tests, the schema, the auth model, and the error envelope — and the documented steps **actually work** as written. Logs are structured, carry a per-request correlation id, and contain **no secrets or full request bodies**. The portfolio write-up exists, with one design decision defended and one failure described.

**Fails when:** any documented command fails; setup requires knowledge not in the README; logs are unstructured prose or unparseable; any log line contains a token, password, or credential.

---

## Also required to pass the gate

All ten criteria, **plus** the portfolio write-up (§C10) — the write-up is inside the gate, not after it. `gates.01-floor.status` moves to `passed` only when both are true.

## Transfer question

Asked at the gate, unscored, recorded in the journal:

> **Same problem, different domain — what changes?** You've built a service that stays up when its database doesn't. If the dependency were a third-party API that is slow rather than absent — degraded, not down — which of your defences still work, and which one becomes actively harmful?
