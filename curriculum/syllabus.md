# Syllabus — AI Engineer

Nine modules, 0 through 8. **Mastery gates, not time gates.** You advance when the grader passes you and the portfolio write-up exists — not when a week ends. There are deliberately no calendar durations in this table; the calendar bends, the bar does not.

Module ordering has one non-obvious choice: **evals come at Module 3**, before retrieval and before agents. Two reasons. It is the largest supply gap in the job market, and after Module 3 you understand the grader that has been judging you — at which point you open its source and improve it.

---

| # | Module | Core concepts | Project → portfolio artifact | Gate highlights |
|---|---|---|---|---|
| **0** | **Bootstrap** | Environment; git discipline; Claude Code internals; agent anatomy by dissection — of this course itself | Operate your campus: run a full session loop, interrupt and resume it, read every state file | Oral defense: explain the tutor's architecture cold; demonstrate resume-from-checkpoint; explain every `mastery.json` field |
| **1** | **The floor** | Backend Python: async/await, concurrency vs parallelism, typing, pytest, FastAPI, Postgres + schema design, Docker, CI, structured logging, debugging *without* AI | Deployed CRUD service with auth, tests, CI, real error handling — **deliberately zero AI features** | Malformed request → structured 4xx, not a traceback; DB down → degrades, doesn't crash; auth boundary covered by tests; CI fails on a seeded bug |
| **2** | **LLM mechanics** | Tokens & sampling; structured outputs; tool calling; streaming; context budgeting; prompt-as-code; multi-provider | Structured-extraction service — messy docs → validated JSON — across two model providers | Handles malformed model output gracefully; prompt changes are versioned and tested |
| **3** | **Evals** | Golden sets; LLM-as-judge; pairwise comparison; regression in CI; retrieval metrics (P@K, nDCG, MRR) | Eval harness for the Module 2 service, **plus a PR improving this course's own grader** | A prompt change measurably moves a metric; published write-up |
| **4** | **Retrieval** | Chunking; embeddings; hybrid BM25 + dense + RRF; reranking; query rewriting; pgvector; ACLs and multi-tenancy | Retrieval system over a messy real corpus, with an eval set and before/after nDCG | Beats a naive RAG baseline on your own eval set; failure analysis published |
| **5** | **Agents** | The loop; tool design as product surface; memory tiers; sub-agents; MCP servers; human-in-the-loop; failure taxonomy; durable execution | An agent doing one genuinely useful thing for real users, plus an MCP server; **and rebuild this tutor's core loop from scratch in raw Python — no framework** | Documented failure taxonomy; the from-scratch loop passes the grader unassisted |
| **6** | **Production** | Cost and latency (caching, routing, parallel calls); OTEL tracing; transcript analysis; guardrails; prompt-injection defense | Public benchmark of the Module 5 agent with a documented 2× cost-or-latency improvement | Traces exist; an injection attempt is caught and logged |
| **7** | **Open-weight stack** | What weights actually are; model anatomy; licenses; MoE total vs active params; quantization; local inference; serving (vLLM/SGLang); open-model agent gotchas; LoRA | **Frontier → open migration:** port the Module 5 agent to an open-weight stack, with measured quality and cost deltas, plus one LoRA'd subtask | Your own eval harness proves the tradeoff; a small model runs locally; write-up quantifies $/quality |
| **8** | **Capstone** | Integration + electives | One system, end to end, for a real user who isn't you; portfolio site assembled from all write-ups | Mock screens: a Stripe-style "debug this failing system" and a Harvey-style agent-design interview |

---

## Status of this syllabus

**Modules 0 and 1 are authored.** Their `concepts.md`, `project.md`, and `rubric.md` are real and gradeable.

**Modules 2–8 are stubs.** The table above is the committed shape, not the finished content. They are deliberately unwritten for two reasons:

1. **Intake hasn't happened.** At the end of Module 0 you declare a **north-star product** — the agent you actually want to exist. The director then *compiles* the curriculum against it: every module project becomes a milestone of your product rather than a generic exercise. Writing those specs now would mean rewriting them all in a few weeks.
2. **Content rots.** In an AI course, staleness is measured in weeks, not semesters. A Module 7 written today is wrong by the time you reach it.

Module 2+ content gets written when you get there, by the director, against your declared north star.

## The dual-track guardrail

Threading everything through one product has a known failure mode: you learn *"my product,"* not *"the discipline,"* and an early architecture mistake compounds for a year. So the course runs roughly **70/30**:

- **Module projects (70%)** — north-star milestones. Cumulative, portfolio-bound.
- **Reps and transfer exercises (30%)** — deliberately generic and disposable, in fresh contexts. The Module 5 from-scratch loop rebuild stays generic by law.

Every gate's oral defense includes one transfer question: *same problem, different domain — what changes?*

## What is not on this syllabus

Kubernetes, Terraform, and a dedicated vector database. The market data says those hours are better spent elsewhere. If a real project demands one, you learn it then — as a tool, not as a module.

## Changing this syllabus

You can't, and neither can the tutor. Module content, rubrics, and gates are read-only to the tutor by constitution — so it cannot quietly make the course easier on a bad day. Curriculum changes are the **director's** power, and every change lands as a git commit with a rationale.

The director is staged for v0.3 and not yet active. Until then, requests to change the course get logged in the journal, where they accumulate as the evidence that activates it.

If you want to skip a module, the answer is never permission — it's `/challenge` (also v0.3): sit the gate, pass it, and the skip is earned rather than granted.
