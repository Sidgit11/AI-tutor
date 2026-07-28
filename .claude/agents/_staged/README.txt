STAGED AGENTS - NOT ACTIVE IN v0.1
==================================

These two agent definitions are here for review, not for use:

  examiner.md.staged  -> v0.2, spaced-repetition quizmaster
  director.md.staged  -> v0.3, course owner (curriculum, appeals, skips, pacing)

Why the `.staged` extension instead of plain `.md`
--------------------------------------------------
SPEC.md §1 offers two ways to stage an agent: mark it `disabled: true` in
frontmatter, or park it in this `_staged/` directory. Neither one actually
works against the runtime:

  1. `disabled` is not a supported subagent frontmatter key. Claude Code
     supports: name, description, tools, disallowedTools, model,
     permissionMode, maxTurns, skills, mcpServers, hooks, memory,
     background, effort, isolation, color, initialPrompt. An unknown
     `disabled: true` is ignored - the agent loads anyway.

  2. Claude Code scans `.claude/agents/` RECURSIVELY. A subdirectory does
     not hide anything; identity comes from the `name:` field, not the path.
     `_staged/examiner.md` would have loaded as a live agent named
     `examiner`.

So the only thing that reliably prevents loading is not being a `.md` file.
Renaming to `.md.staged` keeps the prompts readable and visibly staged while
guaranteeing the runtime never picks them up.

To activate one, drop the `.staged` suffix - and only when its stage trigger
in SPEC.md §1 has actually fired (examiner: the first time the review queue
is non-empty; director: the first disputed grade, skip request, or long
usage gap). Machinery earns its way in.
