# ENGINEERING.md

Practical software engineering guidance for coding and implementation work.

Project-specific conventions may override this file. When they do, follow the project-specific convention and keep changes consistent with the existing codebase.

## General engineering guidance

- Prefer simple, readable code over clever abstractions.
- Keep modules small and focused on one responsibility.
- Separate CLI/parsing concerns from business logic.
- Make behavior testable without invoking the CLI.
- Use clear errors and avoid silent failures.
- Run relevant tests and checks when possible.
- Keep dependencies intentional and minimal.
- Avoid unnecessary abstractions until there is real duplication or complexity.

## Python guidance

- Use type hints for public functions.
- Use dataclasses or typed structures when they make data flow clearer.
- Separate CLI, domain logic, IO, and rendering/reporting.
- Add tests for core logic.
- Keep dependencies minimal and explicit.
