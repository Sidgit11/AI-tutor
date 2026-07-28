# Paste this into Claude Code (run from inside the empty `ai-engineer-course/` folder after copying this kit's contents in)

---

Read `SPEC.md` in this folder completely, then `CONCEPT.md` for background (SPEC wins on any conflict). You are building v0.1 of my AI-engineering tutor — a course system I will use daily.

Build **exactly** what SPEC.md specifies and nothing beyond the v0.1 stage table. No extra mechanisms, dependencies, databases, frameworks, or UI. The agent prompts in `prompts/` are reviewed and final — install them verbatim per SPEC §3; do not rewrite or "improve" them.

**Communication protocol — this is a requirement, not a preference (SPEC §0):**
- Before writing anything, show me your phase plan with a complete file manifest and wait for my approval.
- Check in after every phase: what you built, every decision the spec left open, any deviation you propose. Never deviate silently — proposals wait for my approval.
- When ambiguous, ask me. One-line questions beat plausible guesses.
- One commit per phase: `build(p<N>): <summary>`.
- Finish by running the SPEC §9 acceptance checklist **interactively with me** — demonstrate each of the six items live, including the ones where the tutor must refuse me.

When P4 is reached, ask me for the private GitHub remote URL before pushing.

Start with the P1 plan now.
