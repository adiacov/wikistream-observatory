# AGENTS.md

This repository uses file-based instructions and memory.

Before performing meaningful work:

1. Read `WORKFLOWS.md` and follow it as the primary workflow authority.
2. Read any project memory and planning files referenced by `WORKFLOWS.md`.
3. For coding or implementation work, read and follow `ENGINEERING.md` if present.

When work is completed:

- update project memory as directed by `WORKFLOWS.md`;
- avoid duplicating information across memory files;
- summarize what changed, how it was verified, and any remaining risks.

Project-specific instructions may be added below.

---

## Project-specific instructions

This project uses Spec Kit / specification-driven development. Preserve the spec/plan/task workflow unless the user explicitly changes direction.

Use web research actively when current external facts matter, especially for Wikimedia APIs, EventStreams behavior, schemas, tooling, Docker/uv behavior, or other dependencies that may have changed.

Keep the project framed as responsible observability over public Wikimedia activity. Avoid shallow bot/human dashboards, enforcement claims, accusation-oriented language, or portfolio/reviewer-facing framing unless the user explicitly asks for it.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/001-wikistream-mvp-slice/plan.md`
<!-- SPECKIT END -->
