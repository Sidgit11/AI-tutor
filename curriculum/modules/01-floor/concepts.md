---
module: 01-floor
last_verified: 2026-07-29
verification_note: |
  Version facts below were checked against primary sources on 2026-07-29.
  In this field they rot in weeks. The tutor is required to web-search
  anything vendor-, price-, or version-current rather than trusting this
  file. Where it finds a discrepancy it must say so plainly and teach the
  current truth — it may not edit this file (curriculum is director-owned).
---

# Module 1 — The floor

This module has **zero AI in it.** That is not an oversight; it is the entire point.

The sentence this course is built around comes verbatim from Stripe's screen: *"fluent with AI-assisted development but not dependent on it."* You currently ship with AI assistance. The gap between that and an AI engineer is not prompt technique — it is the backend floor underneath. When your agent times out at 3am, the skill that saves you is reading a traceback and reasoning about connection pools, not writing a better prompt.

So: a deployed CRUD service with auth, tests, CI, and real error handling. Boring on purpose. Everything after this module assumes it.

**Version reality as of 2026-07-29** (verify before relying on any of it):

| Thing | Current | Note |
|---|---|---|
| CPython | 3.14 (3.14.6) | 3.13 also in bugfix. **3.9 is EOL** (2025-10-31) |
| FastAPI | 0.140.13 | |
| Pydantic | 2.13.4 | docs moved to `pydantic.dev/docs/validation/latest/` |
| pytest | 9.1.1 | |
| uv | 0.12.0 | breaking changes since 0.11 |
| PostgreSQL | 18 (18.4) | 19 is **beta** — do not build on it |
| SQLAlchemy | 2.0.51 | 2.1 is beta |
| structlog | 26.1.0 | |
| mypy / pyright | 2.3.0 / 1.1.411 | mypy needs Python ≥ 3.10 |

Your machine's system Python is 3.9.6, which is end-of-life. Do not build on it. Use `uv python pin 3.14` per project — one of the first things this module has you do.

---

## 1. Async, and the distinction everyone gets wrong

### 1.1 Concurrency is not parallelism

This is the most-conflated pair in backend Python, and the one most likely to surface in a screen.

- **Concurrency** — dealing with many things at once. Tasks interleave. One worker, switching between jobs whenever one is waiting.
- **Parallelism** — doing many things at once. Multiple workers, simultaneously, on multiple cores.

A single-threaded async event loop is **concurrent, not parallel**. It can juggle ten thousand open sockets on one core, because sockets spend nearly all their time waiting. It cannot make ten thousand matrix multiplications finish faster, because those spend their time computing.

The operational rule: **async wins on I/O-bound work; processes win on CPU-bound work.** Putting `async` in front of a function that computes for 200ms doesn't make it concurrent — it makes it a 200ms block that stalls every other task on the loop, which is worse than the synchronous version because now it's invisible.

The GIL is why. Historically one CPython thread executes bytecode at a time. **PEP 779 made free-threaded (no-GIL) builds officially supported in 3.14** — but they remain an *optional, non-default* build carrying a ~5–10% single-thread penalty. Treat "Python has no GIL now" as false in any default deployment.
→ https://docs.python.org/3.14/whatsnew/3.14.html

### 1.2 The event loop, concretely

`async def` defines a coroutine. Calling it returns a coroutine object and runs *nothing*. It runs when awaited or scheduled onto the loop.

`await` means: *"I'm about to wait; take my turn."* Control returns to the loop, which runs something else until the awaited thing is ready. Crucially it is **cooperative** — nothing preempts you. A coroutine that never awaits owns the loop until it returns.

What you actually need fluent:

- `asyncio.run(main())` — the entry point.
- `await asyncio.gather(*tasks)` — run many concurrently, collect results in order. Note `return_exceptions`: default `False` means the first exception propagates while the rest keep running unattended.
- `asyncio.TaskGroup` (3.11+) — the modern replacement for most `gather` uses. Structured concurrency: the block doesn't exit until all children finish, and a failure cancels siblings. Prefer it.
- `asyncio.timeout()` / `wait_for` — a call without a timeout is a hang waiting to happen.
- `asyncio.to_thread(fn)` — the escape hatch for blocking calls you cannot avoid.
→ https://docs.python.org/3/library/asyncio.html

### 1.3 Failure modes

- **The blocking call in an async handler.** One `requests.get()` or `time.sleep()` or unwrapped DB driver call, and your whole service serialises. Symptom: latency that degrades under concurrency with the CPU idle. This is the single most common async bug in production Python.
- **Fire-and-forget tasks that vanish.** `asyncio.create_task()` without keeping a reference — the loop may garbage-collect it mid-flight. Exceptions inside a task nobody awaits are swallowed until interpreter exit. Keep references, or use a TaskGroup.
- **Unbounded concurrency.** `gather` over 10,000 items opens 10,000 connections and takes down whatever you're calling. Bound it with a `Semaphore`.
- **Cancellation is an exception.** `CancelledError` propagates through your `try` blocks. Cleanup belongs in `finally`, and swallowing it with a bare `except Exception` breaks shutdown.

---

## 2. Typing

Python's type hints are not enforced at runtime. They exist for **type checkers, editors, and readers** — that is enough to make them worth it, because they catch a whole class of bug before the code runs and they document intent that comments drift away from.

Working set: builtin generics (`list[int]`, `dict[str, int]` — the `typing.List` era is over), `|` unions and `X | None`, `Optional`, `Literal`, `TypedDict`, `Protocol` for structural typing, and `Final`. **PEP 695** gave 3.12+ the `type` alias statement and inline generic syntax (`def f[T](x: T) -> T`); both mypy and pyright support it, mypy only when configured for 3.12+.

**Checkers:** mypy 2.3.0 (requires Python ≥ 3.10) or pyright 1.1.411. Pick one, run it in CI, and turn on strictness incrementally — `disallow_untyped_defs` on a new module is achievable; on a legacy codebase it produces 4,000 errors you will ignore forever.
→ https://docs.python.org/3/library/typing.html · https://mypy.readthedocs.io/

**Pydantic is the runtime half.** Type hints don't validate; Pydantic v2 does — parsing and coercing at your system's boundary, which is exactly where untrusted data arrives. Its core is Rust, so it is fast enough to sit on every request. Know the difference between a *validation* error (bad input → 422) and a *programming* error (bug → 500). Conflating them is how you end up returning 500s for malformed JSON, which C1 of the rubric fails you for.
→ https://pydantic.dev/docs/validation/latest/get-started/ (the old `docs.pydantic.dev/latest/` now redirects here)

---

## 3. pytest

Current: **9.1.1**. → https://docs.pytest.org/

The parts that matter:

- **Plain functions, plain `assert`.** No class hierarchy, no `assertEqual`. Failure introspection is automatic.
- **Fixtures** — dependency injection for tests. `@pytest.fixture` with scopes `function` / `module` / `session`, and `yield` for teardown. `conftest.py` shares them across a directory without imports.
- **`@pytest.mark.parametrize`** — one test, many cases. The fastest way to cover edge inputs honestly.
- **`pytest.raises`** — assert the failure, and assert on the message. A test that only checks the happy path tests nothing about robustness.
- **`monkeypatch`** — patch environment and attributes with automatic undo.

**Async tests:** FastAPI's own documentation now steers you to **anyio's pytest plugin** (`@pytest.mark.anyio`) with `httpx.AsyncClient` + `ASGITransport`, rather than `TestClient`, for async test functions. Do not enable both anyio and `pytest-asyncio` in auto mode — they conflict.
→ https://fastapi.tiangolo.com/advanced/async-tests/

**What good tests look like here** (the rubric grades this): test the **boundary**, not the internals. For this project that means the auth boundary specifically — an unauthenticated request, a request with a malformed token, a token for a different user's resource. Coverage percentage is a vanity metric; a suite at 95% coverage that never tests an authorization failure is worthless.

---

## 4. FastAPI

Current: **0.140.13**. → https://fastapi.tiangolo.com/

Core mechanics: path operations via decorators; **Pydantic models as request/response schemas** (validation and OpenAPI docs fall out of the type hints); `Depends()` for dependency injection, which is where auth, DB sessions, and pagination belong; `lifespan` context manager for startup/shutdown (the old `@app.on_event` is superseded); `BackgroundTasks` for after-response work; `HTTPException` and exception handlers for error shaping.

Sharp edges worth knowing:

- **A `def` path operation runs in a threadpool; an `async def` one runs on the event loop.** So a blocking call in a `def` handler is *fine*, and the same call in an `async def` handler stalls the server. This surprises people constantly. If your DB driver is synchronous, either use `def` handlers or an async driver — do not mix carelessly.
- **Dependencies with `yield`** run teardown after the response. That's how a DB session gets closed reliably.
- **Response models filter output.** `response_model` strips fields not on the model — the mechanism that stops you leaking a password hash because someone added a column.

Recent releases (0.128–0.137) refactored router internals — `APIRouter`/`APIRoute` instances are now preserved, routes can be added after inclusion, and route-building is thread-safe for parallel test runs. If you find an old StackOverflow answer poking at router internals, check it against current docs.

**Error handling is a graded criterion, so be deliberate.** A malformed request must produce a structured 4xx with a machine-readable body — not a stack trace, not a bare 500. Decide your error envelope once (an error code, a human message, optionally a field path) and apply it everywhere via an exception handler. Never let an unhandled exception reach the client with internals in it: that is both a bad experience and an information disclosure.

---

## 5. Postgres and schema design

Current stable: **PostgreSQL 18** (18.4). **19 is in beta** — do not build on it.
→ https://www.postgresql.org/docs/

Schema design is the highest-leverage, least-reversible thing in this module. Application code gets rewritten constantly; a schema mistake is migrated painfully for years.

- **Model the domain, then normalise.** Every table gets a primary key. Foreign keys with deliberate `ON DELETE` behaviour — `CASCADE` and `RESTRICT` encode real product decisions about what deletion means.
- **Constraints are correctness, in the only place that can enforce it.** `NOT NULL`, `UNIQUE`, `CHECK`, and FKs. Application-layer validation is a nicety; two app instances racing will violate a rule that only exists in Python. The database is the last line, and the only one that holds under concurrency.
- **Types honestly.** `timestamptz` not `timestamp` (a naive timestamp is a bug with a delay fuse). `numeric` for money, never `float`. Native `uuid`, `jsonb` not `json`, real enums or a lookup table.
- **Indexes.** A foreign key is not automatically indexed on the referencing side — a classic slow-delete cause. Index what you filter and join on, and know that every index costs write throughput. `EXPLAIN ANALYZE` is how you find out, rather than guessing.
- **Transactions.** ACID, and what isolation level you actually have (Postgres defaults to Read Committed). Know what a transaction holds open, because a long one blocks vacuum and holds locks.
- **Migrations from day one.** Schema changes are code, reviewed and versioned. Alembic is the standard companion to SQLAlchemy.
- **Connection pooling.** Postgres connections are expensive processes. Pool them; understand pool exhaustion, because it is the most likely way this project falls over under load.

**SQLAlchemy 2.0.51** is the mainstream ORM (2.1 is beta). Async support comes via the `sqlalchemy[asyncio]` extra and depends on `greenlet`, which installs by default on common platforms but is not guaranteed on every architecture.
→ https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

**The graded failure mode: DB down.** When the database is unreachable, the service must degrade with a clear error and stay up. It must not crash, must not hang forever on a connection attempt, and must not leak a driver traceback to the client. Set connection timeouts. Decide what a health check reports when the DB is gone. Rubric criterion C2 tests exactly this by killing the database mid-request.

---

## 6. Docker

Package the service so it runs somewhere other than your laptop. *"Works on my machine"* requires a machine it works on.

- **Dockerfile fundamentals** — base image choice (slim vs alpine; alpine's musl libc causes real, confusing wheel problems in Python), layer caching (copy the dependency manifest and install *before* copying source, or you rebuild the world on every edit), `.dockerignore`, and running as a **non-root user**.
- **Multi-stage builds** — build deps in one stage, copy only artifacts into a lean runtime stage.
- **Compose** — `docker compose` (v2, integrated CLI subcommand). The hyphenated `docker-compose` v1 reached **end of life in May 2024** and was removed from GitHub Actions runner images in April 2025. It is dead, not merely discouraged.
- **The `version:` key in compose files is obsolete** — purely informative, and it emits a warning. Compose always validates against the most recent schema. Delete it.
→ https://docs.docker.com/reference/compose-file/version-and-name/

Your local Postgres for this module runs from a compose file. Also: **the twelve-factor rule — config from the environment, never committed.** Secrets in the image are secrets in the registry.

---

## 7. CI with GitHub Actions

CI's job is to fail before your users do.
→ https://docs.github.com/actions

Current facts as of 2026-07-29:

- `actions/checkout` → **v7.0.1**
- `actions/setup-python` → **v7.0.0** — breaking: the `pip-install` input was **removed** in v7
- `ubuntu-latest` → **Ubuntu 24.04**
- **Node 20 action runtime**: runners defaulted to Node 24 from 2026-06-16; Node 20 is **removed 2026-09-16**. Actions still pinned to it will break.
- `set-output` / `save-state` remain deprecated in favour of the `$GITHUB_OUTPUT` / `$GITHUB_STATE` environment files. Old tutorials are full of them.

A minimum honest pipeline for this project: checkout → set up Python → install with `uv` (cached) → lint → type-check → **run tests against a real Postgres service container** → build the Docker image. Tests against a mocked database do not test your schema, and your schema is where the bugs are.

**The graded criterion is adversarial: CI must fail on a seeded bug.** The grader introduces a defect and checks that your pipeline goes red. A green-always pipeline is worse than none, because it is trusted. Verify yours can fail — deliberately break something and watch it catch it.

---

## 8. Structured logging

`print()` is not logging. A log line a machine cannot parse is a log line nobody will read at 3am.

**Structured** means each event is key-value data (rendered as JSON in production), not an interpolated sentence. `logger.info("payment_failed", user_id=..., amount=..., reason=...)` is queryable; `logger.info(f"Payment failed for {user}")` is a grep problem.

- **stdlib `logging`** — loggers, handlers, formatters, levels, and the hierarchy. Configure it once at the edge; never call `logging.basicConfig` inside a library.
- **structlog 26.1.0** — the mainstream structured option. Note `structlog.threadlocal` is **deprecated in favour of `structlog.contextvars`**, which is also what works correctly under async.
→ https://www.structlog.org/en/stable/
- **Correlation IDs.** A request id, generated at the edge, attached to every log line for that request, returned in the response header. Without it, concurrent request logs are interleaved noise. With it, one grep reconstructs the whole story. In async code this belongs in `contextvars`.
- **Levels that mean something.** ERROR = a human should look. WARN = degraded but handled. INFO = business events. DEBUG = off in production.
- **Never log secrets.** Tokens, passwords, full card numbers, entire request bodies. Logs go to third-party aggregators and are retained for years.

---

## 9. Debugging without AI

The named skill of this module, and the one the whole course exists to build. The Stripe-style screen is *"here is a failing system, debug it"* — with no assistant.

**Read the traceback. All of it.** Bottom line is the exception; the frames above are the path. Python reads bottom-up. In async code, tracebacks are noisier and interleaved with loop internals — practise skimming to *your* frames.

**Bisect, don't stare.** Halve the search space repeatedly: does it fail with a smaller input? without the middleware? on a fresh database? `git bisect` does this over history mechanically and is startlingly effective.

**Form a hypothesis, then test *it*.** The failure mode to fight is shotgun debugging — changing four things, seeing it work, and not knowing why. That leaves a bug you'll meet again. State what you believe is wrong, predict what you'd observe if you're right, then look.

**Tools, in order of reach:**
- `logging` at DEBUG with real context — often enough
- `breakpoint()` → pdb: `n` next, `s` step, `c` continue, `p` print, `w` where, `l` list
- `pytest --pdb` drops you into the failing test's frame
- `pytest -x --lf` — stop at first failure, rerun last failures
- For the database: `EXPLAIN ANALYZE`, and `pg_stat_activity` to see what's actually running or blocked

**Reproduce first, always.** A bug you cannot reproduce is a bug you cannot verify you fixed. Turn the reproduction into a failing test *before* fixing — then the test proves the fix and prevents the regression.

**The discipline note.** During this module's reps you will be stuck for stretches with no assistant. That is the training stimulus, not a system failure. The struggle before the hint is what builds the retrieval path — a hint that arrives too early prevents the learning it appears to accelerate. Ask for rung 1 when you're genuinely stuck, and let yourself sit in it a while first.

---

## Sources

Primary docs, verified 2026-07-29:

- Python 3.14 — https://docs.python.org/3.14/whatsnew/3.14.html · asyncio — https://docs.python.org/3/library/asyncio.html · typing — https://docs.python.org/3/library/typing.html
- FastAPI — https://fastapi.tiangolo.com/ · async tests — https://fastapi.tiangolo.com/advanced/async-tests/
- Pydantic — https://pydantic.dev/docs/validation/latest/get-started/
- pytest — https://docs.pytest.org/
- uv — https://docs.astral.sh/uv/
- PostgreSQL — https://www.postgresql.org/docs/
- SQLAlchemy async — https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Docker Compose file reference — https://docs.docker.com/reference/compose-file/version-and-name/
- GitHub Actions — https://docs.github.com/actions · runner images — https://github.com/actions/runner-images
- structlog — https://www.structlog.org/en/stable/
- mypy — https://mypy.readthedocs.io/

Two claims in the research behind this file came back **unverified** and are stated cautiously above: the precise breaking changes in uv 0.12.0, and whether anyio is the recommended async-test default across the wider pytest ecosystem or specifically within FastAPI's docs. Where it matters, check before teaching.
