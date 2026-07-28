---
module: 01-floor
project: Deployed CRUD service with auth
milestones: [M1, M2, M3]
ai_features: none
---

# Module 1 Project — A deployed CRUD service with auth

Build and deploy a real backend service. Authentication, a real database, tests, CI, and error handling that holds up when things break.

## The one non-negotiable constraint: zero AI features

**Nothing in this service may call a model.** No LLM, no embeddings, no "smart" anything. Not as a bonus, not as a stretch goal, not as a small nice-to-have at the end.

This is the constraint people most want to negotiate, so here is the reasoning explicitly. You can already build AI features — that's the baseline you arrived with. What an AI engineer has that you don't yet is the floor underneath: the service that stays up, the schema that doesn't need rewriting, the traceback you can read at 3am. An LLM call inside this project would be the comfortable part, and it would let you skip the uncomfortable part. Module 2 is where models arrive. This module is the floor they stand on.

## Assisted mode

This is a **BUILD (assisted)** project — full AI pair, the way the actual job works. That is not in tension with the constraint above: the tutor may discuss architecture with you, review your code, and debug alongside you. What it will not do, here or anywhere, is write your code. The reps that run alongside this project are the unassisted half.

## A note on the north star

Once intake happens (end of Module 0, run by the director), this project spec compiles against **your declared product** — the CRUD service becomes your product's actual backend skeleton, and it carries forward through every subsequent module.

The director is staged for v0.3 and not yet active, so v0.1 runs this generically. If you already know your north star, build the service around that domain rather than a toy one — the schema and auth model will carry forward and the work compounds. If you don't, pick a domain you understand well; you'll be making schema decisions and you want real intuitions about the entities.

**Rubric criteria never change with the domain.** Only the substrate does.

---

## Requirements

### Functional

- **A resource with full CRUD.** Create, read (single and list), update, delete. Real entities with real relationships — at least two related tables with a foreign key, not one flat table.
- **Authentication.** Users register and log in; endpoints require a valid credential. Token-based, standard mechanism, standard library — do not invent crypto.
- **Authorization, distinctly.** Authentication is *who you are*; authorization is *what you may touch*. A user must not be able to read or modify another user's resources. This is graded separately and specifically, because conflating the two is the most common real-world auth hole.
- **List endpoints paginate.** An endpoint that returns every row is a production incident waiting for a big enough table.

### Non-functional — where the actual grading pressure sits

- **Structured errors.** Every 4xx and 5xx returns a consistent, machine-readable body. Never a stack trace, never framework HTML, never a bare 500 for a malformed request.
- **Degrade, don't crash.** With the database unreachable, the service stays up, answers with a clear error, and does not hang. Connection timeouts are set deliberately.
- **Structured logs with a correlation id** per request, and no secrets in them.
- **Config from the environment.** No credentials in the repo. `.env` is gitignored from the first commit.
- **Migrations.** Schema changes are versioned files, not manual SQL run from memory.

---

## Milestones

Each is separately gradeable — run `/grade` when you reach one rather than saving it all for the end. Failing M1 early is cheap; discovering an M1 problem during M3 is not.

### M1 — Schema and API, running locally

- Postgres 18 running from a `docker compose` file
- Migrations that create the schema from empty
- CRUD endpoints working end to end against the real database
- Auth implemented: register, log in, protected endpoints
- Pydantic models for request and response; the response model does not leak password hashes
- Runs locally with one documented command

**Done when:** you can start from a clean checkout and an empty database, run the documented commands, and exercise every endpoint.

### M2 — Tests and CI, green

- pytest suite against a **real Postgres**, not a mock — a service container in CI
- The auth boundary explicitly tested: no credential, malformed credential, expired credential, and **a valid credential for the wrong user's resource**
- Validation failures tested: wrong types, missing fields, absurd values, oversized payloads
- Type checking (mypy or pyright) and a linter, both in CI
- GitHub Actions pipeline green on push, using current action versions (see `concepts.md` §7 — `actions/checkout` v7, `actions/setup-python` v7 where the `pip-install` input is gone)

**Done when:** CI is green — **and you have proved it can go red.** Deliberately seed a bug on a branch, watch the pipeline fail, then revert. A pipeline never observed failing is not known to work.

### M3 — Deployed and documented

- Deployed somewhere publicly reachable; any host is fine
- Containerised: multi-stage build, non-root user, no secrets in the image
- Environment config in the deployment, not the repo
- A health check that reports honestly — including when the database is gone
- **README** covering: what it does, how to run it locally, how to run the tests, the schema (with a diagram or the DDL), the auth model, and the error envelope
- **A short write-up for the portfolio** — what you built, one design decision you'd defend, and one thing that broke and what you learned. This is part of the gate, not an afterthought.

**Done when:** a stranger can hit the deployed URL, and can go from your README to running it locally without asking you anything.

---

## What gets graded, and how

Read `rubric.md` — you should always know what good looks like.

You may **not** read `curriculum/modules/01-floor/graders/`. It contains the hidden scenarios the grader executes against your service: malformed payloads, auth bypass attempts, connections killed mid-request. Rubrics are public so you know the standard; test inputs are hidden so you build a service that is actually robust rather than one tuned to a known list. Overfitting to visible tests is the exact failure mode evals exist to prevent — you'll build this same public/hidden split yourself in Module 3.

The grader will run your code, run your tests, then run its own cases. A criterion it could not execute is a criterion it will not pass.
