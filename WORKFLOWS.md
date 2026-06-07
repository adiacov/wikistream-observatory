# Workflows

This file is the primary workflow authority. Agent-specific adapter files should only bootstrap the agent into this file, not duplicate its rules.

## Start of session

1. Read the agent adapter/instruction file for the current tool if present.
2. Read project memory files if present, such as `STATE.md` and `BRAINSTORM.md`.
3. Reconcile memory with reality before continuing work:

   - check `sessions/pending/` for raw checkpoint files, ignoring placeholder files such as `.gitkeep`;
   - inspect `git status` and recent commits;
   - inspect project files mentioned by memory, such as briefs, plans, READMEs, specs, and implementation notes;
   - inspect relevant local/external task state when current work mentions tasks;
   - compare these facts with project memory.
4. Treat memory as a hint, not a source of truth. Repository state, task systems, and current project files take precedence.
5. If durable memory is stale or contradicted by repo/task reality, update memory or project docs before continuing normal work.
6. If the task is unclear after reconciliation, ask what we are working on.
7. Read project scope if present, such as `BRIEF.md`, `.specify/memory/constitution.md`, or relevant files under `specs/`.
8. For coding or implementation work, read and follow `ENGINEERING.md` if present.

## Collaboration style

- Work as a collaborative partner, not an autonomous task executor.
- Prefer dialogue over assumptions when requirements, tradeoffs, priorities, or constraints are unclear.
- For non-trivial work, discuss the approach before implementation.
- Present one major decision at a time rather than large batches of options.
- Do not rush into implementation when understanding is incomplete.
- Challenge assumptions when evidence suggests a better approach.
- Keep communication concise and focused.
- When multiple reasonable approaches exist, explain the tradeoffs and recommend one.

## Pending checkpoint handling

If pending checkpoints exist:

1. review them before continuing normal work;
2. extract only durable goals, decisions, current state, next actions, blockers, and important realizations;
3. update project memory/docs as appropriate;
4. move processed checkpoint files to `sessions/archive/`.

If a checkpoint contains only information already reflected in memory/project files, archive it without duplicating content.

Do not blindly copy raw conversation into durable memory.

Checkpoint files are raw recovery evidence, not curated memory. Manual durable-memory updates remain preferred when practical.

A global opt-in checkpoint extension is enabled for this repo via `.pi/checkpoint.json`.
It automatically writes raw shutdown checkpoints to `sessions/pending/` as a safety net.

## Implementation workflow

When coding or editing files:

1. understand the request and affected area;
2. inspect existing files before proposing changes;
3. for non-trivial work, present a short plan;
4. explain intended changes briefly when useful;
5. make minimal, precise edits;
6. preserve existing content unless explicitly asked to reorganize it;
7. run relevant checks when possible;
8. summarize changed files, verification performed, and next steps.

## Spec Kit implementation cadence

Work one phase at a time and stop to reflect at each phase boundary before continuing. Within a phase, complete work in small task-sized pieces and commit after each completed task, including staged documentation/spec updates, so the history stays traceable and recovery is easy.

When using Spec Kit commands or prompts, read the relevant `.pi/prompts/speckit.*.md` file and the active spec artifacts before acting.

## Additional notes

- use web research actively when current external facts matter;
- preserve durable findings in docs or project memory;
- avoid shallow bot/human dashboard framing;
- keep responsible-observability wording: signals indicate activity patterns, not guilt or enforcement decisions.
