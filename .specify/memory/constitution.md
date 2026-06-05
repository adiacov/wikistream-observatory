<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Placeholder Principle 1 -> Specification-First Source of Truth
- Placeholder Principle 2 -> Responsible Wikimedia Observability
- Placeholder Principle 3 -> Local Reproducibility and Free Tooling
- Placeholder Principle 4 -> Testable Data Transformations
- Placeholder Principle 5 -> Narrow Vertical Slices and Simplicity
Added sections:
- Project Constraints
- Development Workflow and Quality Gates
Removed sections:
- None
Templates requiring updates:
- ✅ updated .specify/templates/plan-template.md
- ✅ updated .specify/templates/spec-template.md
- ✅ updated .specify/templates/tasks-template.md
- ✅ checked .specify/templates/commands/; directory not present
- ✅ checked AGENTS.md; no principle-specific update required
Follow-up TODOs: None
-->

# WikiStream Observatory Constitution

## Core Principles

### I. Specification-First Source of Truth

Project intent MUST be captured in Spec Kit artifacts before implementation work begins.
Feature specifications define WHAT and WHY in user/business terms. Implementation plans define HOW
through explicit technical choices and documented rationale. Code, tests, documentation, and demo
artifacts MUST remain traceable to the active specification and plan.

Rationale: this project is both a portfolio artifact and a learning vehicle; disciplined SDD keeps
scope, decisions, and implementation reviewable.

### II. Responsible Wikimedia Observability

The project MUST frame outputs as observability signals, not enforcement decisions or accusations.
Language such as `signal`, `spike`, `automation-like`, `requires review`, and `unusual relative to
baseline` is allowed. Language that labels users as malicious, guilty, abusive, or bad bots is not
allowed unless quoted from Wikimedia documentation with context. Public reports MUST handle
usernames and account-level derived signals responsibly, using aggregation or clear limitations when
appropriate.

Rationale: Wikimedia data is public, but responsible presentation is required to avoid overstating
what stream-derived signals can prove.

### III. Local Reproducibility and Free Tooling

Every MVP feature MUST be runnable locally with documented commands and without paid services.
The project MUST use public/free data sources and free/open tooling. Docker-based local execution
MUST remain the primary reviewer path unless a later constitution amendment changes deployment
scope.

Rationale: recruiters and data engineers must be able to clone, run, and inspect the project without
cloud accounts or hidden infrastructure.

### IV. Testable Data Transformations

Core parsing, normalization, aggregation, and signal-detection logic MUST be covered by automated
tests or equivalent reproducible validation scenarios before being treated as complete. Data quality
behavior MUST be explicit for malformed events, missing fields, duplicate events, event-time versus
processing-time handling, and replay/sample data.

Rationale: the project demonstrates data engineering capability; correctness and reliability of data
transformations matter more than dashboard polish.

### V. Narrow Vertical Slices and Simplicity

Implementation MUST proceed in independently demonstrable vertical slices. The MVP MUST start
with live ingestion, normalized storage, basic metrics, one meaningful signal, and a local dashboard
before adding additional signals or infrastructure. New services, abstractions, dependencies, or
storage systems MUST have a documented need in the plan.

Rationale: a small working observability platform is more valuable than a broad unfinished system.

## Project Constraints

- The system MUST NOT write to Wikimedia or attempt to block, classify, or report editors for
  enforcement action.
- The MVP MUST NOT depend on paid APIs, paid cloud services, Kubernetes, historical backfills, or
  complex ML services.
- Major Wikimedia API, stream, schema, rate-limit, or bot-policy assumptions MUST be checked
  against current documentation or live behavior before implementation.
- Documentation MUST explain assumptions, limitations, and ethical boundaries for derived signals.

## Development Workflow and Quality Gates

- Before coding, the active feature MUST have a completed `spec.md`, `plan.md`, and `tasks.md`.
- `/speckit.plan` MUST include a Constitution Check covering responsible framing,
  reproducibility, free tooling, testable transformations, and vertical-slice simplicity.
- `/speckit.tasks` MUST generate independently testable user-story phases and include validation
  tasks for data transformations, demo/replay behavior, documentation, and local run commands.
- Implementation MUST run relevant checks when available and update project memory when durable
  state or decisions change.

## Governance

This constitution supersedes conflicting project practices and guides all Spec Kit artifacts,
implementation plans, and review decisions. Amendments MUST update this file, include a Sync Impact
Report, and propagate changed requirements to templates or runtime guidance where needed.

Versioning follows semantic versioning:

- MAJOR for incompatible changes to principles or project governance.
- MINOR for new principles, new required sections, or materially expanded guidance.
- PATCH for clarifications, wording fixes, or non-semantic refinements.

Compliance review is required during planning and before implementation. Any deliberate violation
MUST be recorded in the implementation plan with rationale and a simpler alternative that was
rejected.

**Version**: 1.0.0 | **Ratified**: 2026-06-05 | **Last Amended**: 2026-06-05
