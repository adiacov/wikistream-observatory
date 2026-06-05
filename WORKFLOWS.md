# Workflows

## Start of session

1. Read the agent adapter/instruction file for the current tool if present.
2. Read project memory files if present, such as `STATE.md` and `BRAINSTORM.md`.
3. Reconcile memory with reality before continuing work:
   - check `sessions/pending/` for raw checkpoint files;
   - inspect `git status` and recent commits;
   - inspect project files mentioned by memory, such as briefs, plans, and READMEs;
   - inspect relevant local/external task state when current work mentions tasks;
   - compare these facts with project memory.
4. If durable memory is stale or contradicted by repo/task reality, update memory or project docs before continuing normal work.
5. If the task is unclear after reconciliation, ask what we are working on.
6. Read project scope if present, such as `BRIEF.md`.

## Pending checkpoint handling

If pending checkpoints exist:

1. review them before continuing normal work;
2. extract only durable goals, decisions, current state, next actions, blockers, and important realizations;
3. update project memory/docs as appropriate;
4. move processed checkpoint files to `sessions/archive/`.

Do not blindly copy raw conversation into durable memory.

Checkpoint files are raw recovery evidence, not curated memory. Manual durable-memory updates remain preferred when practical.

## Implementation workflow

When coding or editing files:

1. inspect existing files before changing them;
2. explain intended changes briefly when useful;
3. make minimal, precise edits;
4. preserve existing content unless explicitly asked to reorganize it;
5. run relevant checks when possible;
6. summarize changed files and next steps.

## Spec Kit implementation cadence

Work one phase at a time and stop to reflect at each phase boundary before continuing. Within a phase, complete work in small task-sized pieces and commit after each completed task, including staged documentation/spec updates, so the history stays reviewable and recovery is easy.

## Additional notes

- use web research actively
- preserve findings in docs
- avoid shallow bot/human dashboard
