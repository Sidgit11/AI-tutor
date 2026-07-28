# The Tutor — Concept Note
### A local-first AI tutor that teaches you AI engineering, grades your work, and builds your portfolio as a side effect

**For:** Siddhant · **Date:** 28 July 2026 · **v1 substrate:** Claude Code native · **Baseline:** ships with AI assistance · **Pace:** 5–10 hrs/week (~10–12 months to full portfolio)

---

## 0. The core idea in three sentences

A persistent tutor agent that lives in a git repo on your machine, holds a **student model** of what you actually know, teaches via mastery gates and Socratic escalation, and hands every project to a **separate adversarial grader agent** so it can never grade its own teaching. Every module ends in a shipped, public artifact — the portfolio assembles itself. And the bootstrap trick: **the tutor is your first agent project**, so you're learning agent architecture from day 0 by inspecting the thing teaching you.

One design constraint drives everything, and it comes straight from your JD research (Stripe's screen, verbatim): *"fluent with AI-assisted development but not dependent on it."* You currently ship **with** AI assistance. The course's explicit job is to convert that into competence that survives a whiteboard. So the tutor enforces **unassisted reps** — some work happens with Claude's hands tied behind its back.

---

## 1. What to steal from existing systems (the inspiration map)

| Source | What it proves / what we take |
|---|---|
| **Bloom's 2-sigma problem (1984)** | 1:1 mastery tutoring moves students ~2 standard deviations above classroom teaching. This is the thesis: LLMs make 2-sigma tutoring free. Everything else is implementation. |
| **Andrew Ng's courses** | The real innovation wasn't the lectures — it was the **autograder**. Worked example → assignment → automated, objective feedback. We replicate the autograder as an eval harness (which is itself a course topic — see the meta-trick below). |
| **Math Academy** | Best-in-class adaptive system design: diagnostic first, a knowledge graph with per-concept mastery scores, spaced review woven into new material, XP for momentum. We steal the **student model + review queue** architecture wholesale. |
| **Khanmigo (Khan Academy)** | Socratic by policy — refuses to hand answers, asks the next question instead. We steal the policy but add an **escalation ladder** (pure Socratic forever is rage-inducing for adults; see §4). |
| **CS50's AI duck (ddb)** | Guardrailed TA: helps you debug, banned from writing your solution. We steal the hard ban on the tutor writing project code. |
| **fast.ai (Jeremy Howard)** | Top-down pedagogy: play the whole game first, theory second. Ship a working thing in session 1 of every module, then descend into mechanism. Never "12 weeks of foundations before you touch anything real." |
| **Exercism** | The mentor-feedback loop on small exercises: submit → human-quality critique → iterate. Our grader agent does this per-exercise, not just per-project. |
| **Anki / FSRS** | Spaced repetition against forgetting. Concepts you learned in week 3 get quizzed in weeks 5, 9, 17 — scheduled by the student model, executed by a quizmaster agent. |
| **Cognitive apprenticeship** | Modeling → scaffolding → fading. The tutor demonstrates first, assists second, then deliberately withdraws. The fading is scheduled, not vibes-based. |
| **ChatGPT Study Mode / Claude learning styles** | The cautionary tale, not the model. They're stateless — no student model, no projects, no grader, no portfolio. Good bedside manner, no spine. Ours is the opposite trade. |

**The meta-trick worth naming:** the grader agent that scores your projects is an LLM-as-judge eval harness with rubrics, golden cases, and regression tracking. That's Tier-2 curriculum content from your JD research (43% of JDs, the market's biggest supply gap). You learn evals by *being subject to them*, then in Module 3 you open the grader's own source and improve it. The campus is the curriculum.

---

## 2. Operating principles (the tutor's constitution)

1. **Mastery gates, not time gates.** You advance when the grader passes you, not when the week ends. Self-paced means the calendar bends, never the bar.
2. **The tutor teaches; the grader judges. Never the same agent.** A tutor that grades its own teaching drifts sycophantic within a week. The grader is a separate subagent, prompted to find what breaks, running your code against cases you haven't seen.
3. **Socratic by default, generous on schedule.** Escalation ladder per stuck-point: (1) a question → (2) a concept pointer → (3) a worked *analogous* example → (4) full walkthrough of the concept — but **never paste-able code for the active project**. You can always invoke rung 4 explicitly; the tutor logs it as a signal, not a sin.
4. **Everything runs.** No notebook-only work, no pseudo-code answers accepted. "It works on my machine" requires a machine it works on.
5. **Assisted and unassisted modes are both first-class.** Each module has *reps* (unassisted: tutor watches, hints only, no code written for you) and *builds* (assisted: full AI pair, because that's how the actual job works too). The ratio shifts toward unassisted early, back toward assisted late — because the job is Stripe's sentence: fluent with it, not dependent on it.
6. **Three-pass teaching for every concept:** intuition (why it exists) → mechanism (how it works) → production failure modes (how it breaks). The third pass is what separates JD-grade knowledge from tutorial knowledge.
7. **Every module emits a portfolio artifact.** Not "finish the course then build a portfolio" — the write-up is part of the mastery gate.
8. **The student model is sacred.** Every session reads it at start and writes it at end. If it's not in the model, it didn't happen.
9. **Simplicity is a hard constraint, not a preference.** Three enforcement rules: **(a) One Door** — the student only ever needs `/standup`; every other mechanism is discoverable through conversation, never required knowledge. **(b) Machinery earns its way in** — the system ships staged (v0.1 = tutor + grader only; examiner at v0.2; director, challenge, appeals at v0.3), and each mechanism is added only when its absence has produced a *logged* pain point, not a hypothetical one. **(c) Complexity budget, director-owned** — any new mechanic must delete or absorb an existing one, or trace to a journal entry proving need; a monthly sunset review removes anything unused. Corollary: if a rule isn't enforced by a file or an agent, it doesn't exist — aspirational process is deleted on sight.

---

## 3. Architecture — the campus repo

One git repo. Claude Code is the runtime; the repo is the state.

```
ai-engineer-course/
├── CLAUDE.md                      # tutor constitution: persona, protocol, hard rules
├── .claude/
│   ├── skills/
│   │   ├── standup/SKILL.md       # /standup — opens every session
│   │   ├── teach/SKILL.md         # three-pass concept teaching protocol
│   │   ├── rep/SKILL.md           # unassisted exercise mode (hands-tied rules)
│   │   ├── grade/SKILL.md         # invokes grader on a project/exercise
│   │   ├── quiz/SKILL.md          # spaced-repetition review session
│   │   └── shipit/SKILL.md        # module close: portfolio write-up + gate check
│   └── agents/
│       ├── grader.md              # adversarial evaluator (see §5)
│       ├── examiner.md            # quizmaster for spaced review
│       └── director.md            # course owner: feedback, appeals, skips, curriculum changes (see §9)
├── curriculum/
│   ├── syllabus.md                # module map + mastery gates
│   ├── CHANGELOG.md               # every course change: what, why, which agent — auditable
│   └── modules/01..08/
│       ├── concepts.md            # source-of-truth notes (tutor teaches FROM these, cites them)
│       ├── project.md             # spec + milestones
│       ├── rubric.md              # observable pass criteria — you can read it
│       └── graders/               # hidden test cases & eval scripts — you agree not to open
├── student/
│   ├── profile.md                 # goals, constraints, baseline, target roles
│   ├── state.json                 # in-flight session checkpoint + parking lot (crash-safe resume)
│   ├── mastery.json               # the student model (schema below)
│   ├── misconceptions.md          # standing log of your recurring error patterns
│   └── journal/YYYY-MM-DD.md      # session logs, auto-written at close
├── projects/                      # real repos; each one a portfolio piece
└── portfolio/                     # auto-assembled index + write-ups → later a public site
```

**`mastery.json` — the student model schema:**

```json
{
  "concepts": {
    "async-python": {
      "mastery": 0.7,
      "last_touched": "2026-08-02",
      "next_review": "2026-08-09",
      "evidence": ["rep-012 passed 5/6", "project-1 grader: retry logic correct"],
      "misconceptions": ["conflated concurrency with parallelism, session 4"]
    }
  },
  "mode_ratio": {"unassisted_reps_this_module": 6, "assisted": 4},
  "escalations": [{"date": "2026-08-02", "concept": "asyncio", "rung": 3}],
  "streak": 12
}
```

**CLAUDE.md — the constitution, core excerpt (draft to refine when we build):**

> You are my AI-engineering tutor. Non-negotiable rules:
> 1. Open every session by reading `student/mastery.json` and the last journal entry. Close every session by updating both.
> 2. If review items are due, they come before new material. Always.
> 3. You never write code for the active project or rep. Escalation ladder: question → concept pointer → analogous worked example → concept walkthrough. Log every rung-3+ escalation to the student model.
> 4. You never grade. Grading is `/grade`, which spawns the grader agent. You may disagree with the grader's verdict in discussion, but you cannot overturn it.
> 5. In rep mode you are hands-off: hints only, and you flag me if I paste in AI-generated code — reps are unassisted by definition.
> 6. Teach every concept in three passes: intuition, mechanism, production failure modes. Check understanding with a question before advancing each pass.
> 7. Cite `curriculum/modules/*/concepts.md` when teaching; search the web for anything version- or vendor-current rather than answering from memory.
> 8. Mastery gates are hard gates. No module advance without a grader pass and a portfolio write-up.

---

## 4. The session loop (designed for your 60–90 min blocks)

```
/standup            →  tutor reads state, proposes the block:
                        [due reviews: 10 min] → [teach or project: 45–60] → [close: 10]
  1. REVIEW          examiner runs due spaced-rep items; results → mastery.json
  2. TEACH / BUILD   new concept (three passes) or project milestone work
  3. REP (2–3×/wk)   one unassisted exercise, 15–25 min, tutor observing
  4. /grade          when a milestone or rep is done — grader returns scored rubric
  5. CLOSE           journal written, mastery updated, next session pre-planned
```

Weekly rhythm at 5–10 hrs: **four 90-min blocks + one "demo Friday"** — 30 minutes where you show the week's artifact to the tutor and it plays skeptical interviewer ("walk me through why you chose X"). That interview rep is deliberate: it trains the *explaining* muscle that screens actually test, and it's free spaced repetition.

---

## 5. The grader — the component that makes this real

The single failure mode that kills every "ChatGPT is my tutor" attempt is **grade inflation**. An agent that likes you will tell you your RAG pipeline is great. Design against it structurally, not by prompt-wishing:

- **Separate agent, separate prompt, adversarial stance.** "Your default is to find what breaks. A pass must be earned against the rubric, criterion by criterion. When uncertain, fail the criterion and say why."
- **It runs the code.** Grading = executing your project against `graders/` cases: edge inputs, malformed data, a load blip, an injection attempt. Not code-reading vibes.
- **Hidden cases.** Rubrics are public (you should know what good looks like); test inputs are not (you shouldn't overfit to them). The grader can also generate fresh cases per run.
- **Rubrics are observable, not aesthetic.** Not "clean code" but "retries with backoff on 429s; a malformed tool-call response doesn't crash the loop; p95 latency under X on the provided corpus."
- **Structured verdict:** per-criterion pass/fail + evidence + the single highest-leverage gap → appended to `mastery.json`. Fail = a targeted remediation plan from the tutor, then regrade. Failing is the system working.

---

## 6. Syllabus v1 — eight modules, mapped from the 88-JD research

Ordering note: **evals come early (Module 3)**, before retrieval and agents — because they're the market's biggest gap *and* because after Module 3 you understand your own grader, and start improving it.

| # | Module | Core concepts | Project → portfolio artifact | Gate highlights |
|---|---|---|---|---|
| 0 | **Bootstrap** (wk 1–2) | Environment, git discipline, Claude Code internals, agent anatomy by dissection | **Build the tutor itself** from this note — repo, CLAUDE.md, skills, grader v0 — and declare your **north-star product** at intake (§6.5) | Tutor runs a full session loop; you can explain its architecture cold; `northstar.md` written and curriculum compiled |
| 1 | **The floor** (wk 3–8) | Backend Python: async, typing, pytest, FastAPI, Postgres, Docker, CI, debugging *without* AI | Deployed CRUD service with auth, tests, CI — deliberately zero AI in it | 60% of module reps unassisted; you debug a seeded broken service live |
| 2 | **LLM mechanics** (wk 9–13) | Tokens & sampling, structured outputs, tool calling, streaming, context budgeting, prompt-as-code, multi-provider | A structured-extraction service (messy docs → validated JSON) across two model providers | Handles malformed model output gracefully; prompt changes are versioned + tested |
| 3 | **Evals** (wk 14–18) | Golden sets, LLM-as-judge, pairwise, regression in CI, metrics (P@K, nDCG, MRR) | Eval harness for Module 2's service **+ a PR improving the course's own grader** | A prompt change measurably moves a metric; published write-up |
| 4 | **Retrieval** (wk 19–25) | Chunking, embeddings, hybrid BM25+dense+RRF, reranking, query rewriting, pgvector; ACLs & multi-tenancy | Retrieval system over a messy real corpus (Wyra's docs are a legitimate candidate) with eval set + before/after nDCG | Beats naive RAG baseline on your own eval set; failure analysis published |
| 5 | **Agents** (wk 26–33) | The loop, tool design as product surface, memory tiers, sub-agents, MCP servers, HITL, failure taxonomy, durable execution | An agent doing one genuinely useful thing for real users + an MCP server; **rebuild your tutor's core loop from scratch in raw Python** — no framework | Documented failure taxonomy; the from-scratch loop passes the grader unassisted |
| 6 | **Production** (wk 34–39) | Cost/latency (caching, routing, parallel calls), OTEL tracing, transcript analysis, guardrails, injection defense | Public benchmark of your Module-5 agent with a documented 2× cost-or-latency improvement | Traces exist; an injection attempt is caught and logged |
| 7 | **Open-weight stack** (wk 40–46) | What weights actually are, model anatomy, licenses, quantization, local inference, serving (vLLM/SGLang), open-model agents, LoRA fine-tuning | **Frontier→open migration:** port your Module-5 agent to an open-weight stack, with measured quality and cost deltas + one LoRA'd subtask | Your own eval harness proves the tradeoff; a small local model runs on your laptop; write-up quantifies $/quality |
| 8 | **Capstone** (wk 47–52) | Integration + electives | One system, end-to-end, for a real user who isn't you; portfolio site assembled from all write-ups | Mock screens: the tutor runs Stripe-style ("debug this failing system") and Harvey-style (agent design) interviews |

Weeks are elastic — mastery gates govern. Your baseline likely compresses Module 2 and stretches Module 1: the unassisted floor is precisely where "ships with AI assistance" needs the reps.

### 6.5 The north-star project — the course compiles itself around YOUR product

The single biggest design upgrade over a fixed curriculum: at intake (Module 0), the student declares a **north-star product** — the agent they actually want to exist. *"An AI GTM engineer." "An AI project manager." "A trade-compliance analyst agent."* The director records it in `student/northstar.md` (target user, core job-to-be-done, tool surface, data sources, one success metric) and then **compiles the curriculum against it**: every module's project spec is a template with north-star slots, so module projects become milestones of the student's own product rather than generic exercises.

For an "AI GTM engineer" north star, the same syllabus renders as:

| Module | Generic spec | Compiled against the north star |
|---|---|---|
| 1 · Floor | CRUD service | The GTM agent's backend skeleton: accounts/contacts schema, auth, CI |
| 2 · LLM mechanics | Extraction service | Messy prospect data → validated ICP profiles (structured outputs, tool calls) |
| 3 · Evals | Eval harness | Golden set of real prospect cases; "did it qualify this lead correctly?" as a measured metric |
| 4 · Retrieval | RAG over a corpus | Retrieval over CRM notes, call transcripts, ICP docs — ACL-aware from day one |
| 5 · Agents | A useful agent + MCP server | The GTM agent v1: research → qualify → draft outreach, with HITL approval; MCP server exposing its tools |
| 6 · Production | Benchmark + guardrails | The GTM agent hardened: cost per lead processed, latency budget, injection defense on inbound content |
| 7 · Open-weight | Migration project | The GTM agent's router: local small model for classification, hosted open MoE for drafting |
| 8 · Capstone | Integration | **v1 launch to a real user** — the product exists, with 8 graded milestones behind it |

**The transfer guardrail (why this isn't just one long project).** Threading everything through one codebase has a known failure mode: you learn *"my GTM agent,"* not *"agents,"* and an early architecture mistake compounds for a year. So the course runs dual-track, roughly 70/30:

- **Module projects (70%)** → north-star milestones, cumulative, portfolio-bound.
- **Reps and transfer exercises (30%)** → deliberately generic and disposable, in fresh contexts. The Module-5 from-scratch agent-loop rebuild stays generic by law. And each gate's oral defense includes one transfer question: *"same problem, different domain — what changes?"*

**Pivot rule:** the north star can pivot once, via the director, with an explicit migration-cost conversation — exactly like a real product. Rubrics never change with the north star; only the substrate does. Mastery criteria are product-agnostic; the product is what makes them worth meeting.

### 6.6 The open-weight track (Module 7) — expanded

This module exists for two reasons: it's the deepest way to **demystify what a model actually is**, and it's a genuine market differentiator (33% of production teams deploy their own open-source models per LangChain's survey; inference-stack skills gate the entire infra-company track in the JD data). One honest caveat carried from the research: open source is **11% of enterprise LLM spend and falling** (Menlo) — so this is Module 7, not Module 2. You learn it after the applied core, as leverage, not as the foundation.

**Concept spine (what the tutor teaches):**
1. **What weights are.** A model is a giant array of learned numbers — the parameters of a transformer (embedding matrices, attention heads, MLP blocks). The multi-GB file you download from Hugging Face *is* the model: weights (`safetensors`) + config + tokenizer + chat template. Demystification exercise: open a small model's tensors in Python, inspect shapes, trace one token through one layer.
2. **Open weights ≠ open source.** You get the numbers, usually not the training data or code. Licenses matter and vary: MIT (GLM-5.2, DeepSeek V4), Apache 2.0 (Qwen3-Coder-Next, Mistral Small/Large), modified MIT (Kimi K2.6, Inkling ecosystem terms). License reading is a product skill, not a legal afterthought.
3. **The MoE reality — total vs active parameters.** The 2026 open frontier is Mixture-of-Experts: Inkling is 975B total / 41B active; DeepSeek V4 Pro is 1.6T/49B; Kimi K2.6 is 1T/32B; GLM-5.2 is 753B/40B. Only a fraction of the network fires per token — which is why these are affordable to serve and why "billion parameters" alone tells you little.
4. **The hardware truth.** Your MacBook Air runs quantized small models (~≤30B, via Ollama or MLX) — great for routing, classification, drafting subtasks. The frontier-class open MoEs run via hosted inference (Together, Fireworks, Baseten, Modal, OpenRouter) or rented GPUs. "Open" mostly means *portable and inspectable*, not *free on your laptop*.
5. **Quantization.** FP16 → INT8/INT4, GGUF/MLX/NVFP4 formats, what you pay in quality for what you save in memory — measured with your Module-3 eval harness, not vibes.
6. **Serving.** vLLM and SGLang, batching, KV cache, why throughput ≠ latency. This is the 14%-of-JDs infra vocabulary (Fireworks, Modal, NVIDIA) at working-literacy depth.
7. **Open-model agent gotchas.** Chat templates differ per family; tool-calling reliability varies far more than on frontier APIs; structured-output support is uneven. Your agent's harness from Module 5 gets hardened here.
8. **Fine-tuning, finally earned.** LoRA/QLoRA on a small model for one narrow subtask; Tinker (Thinking Machines' fine-tuning platform, where Inkling is the native base) as the managed path. Gate: the tuned model must beat your prompt-only baseline on your own evals.

**The project — frontier→open migration.** Take the Module-5 agent. Build a router: a small local model (e.g., Qwen3-Coder-Next class, quantized, on your Mac) handles cheap subtasks; a hosted open MoE (Kimi K2.6 / GLM-5.2 / DeepSeek V4 / Inkling) handles the hard ones. Run your eval suite against the frontier-API version. Publish the write-up: quality delta, cost delta, latency delta, and where the open stack broke. That artifact — *"migrated a production agent to open weights at X% quality and Y% cost, with evidence"* — is rare, current, and exactly the shape of claim the market can't ignore.

---

## 7. Install list (Module 0, session 1 — tutor walks you through it)

- **Core:** git + GitHub (Actions for CI), `uv` + Python 3.12, Node LTS, Docker Desktop
- **Data:** Postgres 16 + pgvector via one `docker-compose.yml` (used from Module 1 onward)
- **AI:** Claude Code (runtime), Anthropic API key + one second provider (multi-model is a stated JD expectation), Braintrust or LangSmith free tier (Module 3)
- **Later, when the module demands it:** OTEL collector + Grafana (Module 6); Ollama or LM Studio (MLX backend for Apple silicon), a Hugging Face account, an OpenRouter or Together key, and a GPU-rental account (Modal/RunPod) for Module 7. Explicitly **not** installing: Kubernetes, Terraform, a dedicated vector DB — the JD data says don't spend your hours there.

---

## 8. Failure modes we're designing against

| Trap | Structural counter |
|---|---|
| Sycophantic grading | Separate adversarial grader, hidden cases, executable rubrics (§5) |
| Tutor leaks the answer | Hard ban on project code + escalation ladder + escalation logging |
| Learning to prompt, not to build | Rep mode: unassisted exercises with the tutor's hands tied, ratio tracked in the student model |
| Illusion of competence (recognize ≠ recall) | Spaced-rep examiner + demo-Friday verbal defense |
| Motivation decay at self-pace | Streaks, standups, weekly shipped artifact, and the fact that stopping mid-module leaves a visible open gate |
| Tutor hallucinating stale facts | Teaches from `concepts.md` with citations; web-search mandate for anything vendor-current |
| Portfolio procrastination | Write-up is inside the mastery gate, not after it |

---

## 9. UX bottlenecks & the control plane

The pedagogy can be right and the experience still die of operational friction. These are the failure modes that kill self-paced systems, clustered, each with a structural answer — including the course-director role, formalized.

### 9.1 Separation of powers — four agents, four jobs

| Agent | Owns | Write access | You talk to it when |
|---|---|---|---|
| **Tutor** | the session (tactical) | student model, journal | learning, building |
| **Grader** | verdicts (per artifact) | mastery evidence | a milestone is done |
| **Examiner** | retention | review queue | (invoked by standup) |
| **Director** | the course itself (meta) | `curriculum/`, syllabus, rubrics, CHANGELOG | feedback, skips, appeals, pacing, "this isn't working" |

Three rules make this a system instead of a role-play: the **tutor cannot edit the curriculum** (so it can't quietly make the course easier when you're frustrated), the **tutor cannot overturn the grader** (already law), and **only the director changes the course — every change a git commit** in `curriculum/CHANGELOG.md` with a rationale. Auditable, reversible, and immune to in-the-moment negotiation, because the director acts *between* sessions, not during frustration.

**Weekly retro (10 min, replaces nothing — added to demo Friday):** the director reads the week's telemetry (escalation counts, rep durations, fail patterns, session frequency — all already in `mastery.json`), asks you three feedback questions, and ships course adjustments as commits. Your feedback loop to the course has a named owner and a visible output.

### 9.2 Session lifecycle — mid-session exits, sprawl, tiny windows

- **Crash-safe by construction.** State writes at every *step boundary* (checkpoint to `state.json`, journal appended as-you-go), never only at session close. Quitting mid-session — kid, meeting, dead battery — costs nothing. Next `/standup`: *"You were 20 minutes into pass 2 of tool calling. Resume, or restart the pass?"*
- **Hard timebox with a parking lot.** At minute 80 of 90 the tutor lands the plane. Open threads go to the parking lot in `state.json` and are pre-loaded into the next session's plan. Sessions never sprawl; threads never silently drop.
- **Small windows are first-class.** `/standup 20` produces a legitimate 20-minute session (due reviews, or one rep) instead of a guilt trip about the full loop. A bad week with three 20-minute sessions still moves the mastery file.
- **Context-compaction immunity.** All state lives in files, never in the conversation. If the runtime compacts mid-session, the constitution requires a silent state re-read. The session survives its own infrastructure.

### 9.3 Stuck loops — the same thing keeps happening

- **Three-strikes modality rule.** If a concept fails three times (rep, gate, or review), the tutor is *barred* from re-teaching it the same way. It must switch modality — different analogy domain, smaller decomposition, or a micro-project detour — and log the switch. Repeating the same explanation louder is the canonical bad-tutor failure; here it's constitutionally illegal.
- **Repetition detection.** The journal records what's been taught. The constitution bans re-delivering an explanation that already exists in the journal — reference and extend, don't replay.
- **Plateau vs. gate disagreement.** If *you* feel done but the gate disagrees, you don't argue with the tutor — you take the challenge exam (§9.4). Feelings don't move gates; evidence does, in both directions.

### 9.4 Skipping and reordering — demonstrate, don't ask

- **`/challenge <module>`** — the elegant answer to "I want to skip this chapter." It sends you straight to the module's gate: the grader runs the project rubric, the tutor runs the oral defense. Pass → module marked mastered, skip earned, evidence recorded in `mastery.json`. This deletes the permission conversation entirely: the answer to "can I skip?" is always *"show me."* No fiat, no self-deception, no negotiation.
- **Curriculum-level changes** (drop an elective, reorder modules, inject a Tradyon-relevant topic) are a director conversation. The director edits the syllabus and commits the decision with rationale — so six months later you can see what changed and why.

### 9.5 Life happens — gaps, re-entry, burnout

- **The comeback protocol.** `/standup` after a 10+ day gap auto-switches mode: zero guilt language, a decay-aware re-diagnostic on stale concepts, and a deliberately *easy* first session back (one rep you'll pass, plus reviews). Re-entry dread is the #1 killer of self-paced learning; the design answer is making the first session back cheap and winnable.
- **Streaks freeze, never reset,** for declared breaks. Punitive streak mechanics backfire on adults with companies to run.
- **Overpace detection.** The director watches session density and rep error rates; rising errors with rising hours triggers a suggested deload week. Burnout is a telemetry pattern before it's a feeling.

### 9.6 Trust and fairness — when the grader is wrong

- **`/appeal`** routes to the director — never the tutor — who re-runs the grading with the full transcript and evidence. Confirmed grader bug → rubric or hidden test fixed, commit logged, verdict amended. Appeals must exist or trust collapses on the first bad call; they must bypass the tutor so sympathy can't leak into verdicts. LLM judges *do* misfire — the system's credibility rests on having a fair court, not a perfect one.
- **Canary calibration.** Monthly, the director re-grades one previously *passed* artifact. Drift in either direction (model updates making the grader softer or harsher) gets caught by design, not by vibes.
- **Content rot.** Every `concepts.md` carries a last-verified date; the director runs a monthly refresh pass (web check on models, tools, prices). In an AI course, staleness is measured in weeks — Inkling didn't exist twelve days ago.

### 9.7 Orientation and motivation

- **`/map`** — one glanceable render: the mastery graph, gates passed, artifacts shipped, current position, next gate. Invisible progress kills self-paced courses as reliably as difficulty does; this is the antidote you can open in ten seconds.
- **Demo Friday can go public.** Write-ups push to the portfolio site on a cadence the director owns — one decision, made once, not a daily willpower tax.

### 9.8 The command surface — kept deliberately tiny

Command sprawl is itself a UX bottleneck. Everything routes through **five verbs**, and plain conversation always works — commands are shortcuts, not requirements:

> `/standup [minutes]` (start · resume · comeback — it detects which) · `/grade` · `/challenge <module>` · `/director` (feedback · appeal · skip · pacing · anything meta) · `/map`

---

## 10. Build plan — this weekend

1. **(90 min)** `mkdir ai-engineer-course` → scaffold the tree in §3, draft CLAUDE.md from the excerpt, create `mastery.json` seeded from your honest baseline.
2. **(60 min)** Write `standup`, `teach`, and `grade` skills v0. Grader agent v0 = rubric + "run it and try to break it" prompt. Director v0 = a one-page agent prompt with curriculum write access + the CHANGELOG convention; `state.json` checkpointing goes into the standup skill from day one (crash-safety is cheap now, expensive later).
3. **(60 min)** Port the 8-module syllabus into `curriculum/`, write Module 0–1 `concepts.md` stubs (I can generate first drafts).
4. **(30 min)** Run the first real session: `/standup` → Module 0 → the tutor teaches you its own anatomy.
5. Iterate the constitution weekly — it will be wrong in specific ways only usage reveals, and tuning it is itself agent-design practice.

---

## 11. Productization — parking lot (deliberately short)

The durable assets, if this ever becomes a product, are exactly the parts no wrapper startup has: the **student-model schema**, the **rubric library with hidden case banks**, the **escalation-ladder pedagogy**, the **grader-separation pattern**, and — sharpest of all — the **north-star compiler** (§6.5). The productized promise isn't "learn AI engineering"; it's *"declare the agent product you want to exist, and graduate with it shipped."* A student who finishes doesn't hold a certificate — they hold a working AI GTM engineer, or AI PM, or whatever they declared at intake, with eight graded milestones behind it. That's a category-of-one position against every course and every course-shaped chatbot. The harness (Claude Code today) is replaceable; the curriculum + evaluation + compilation IP is not. Get the single-user experience to 2-sigma first. Revisit after Module 3, when you'll have opinions grounded in usage — and an eval harness to prove them.
