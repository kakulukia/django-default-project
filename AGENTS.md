# AGENTS.md

## Communication

- Reply directly and concisely.
- No pleasantries.
- Do not restate the question.
- Use bullet points when they make the answer clearer.
- Push back actively when assumptions are risky, wrong, or incomplete.
- Ask clarifying questions on technical objections before implementing risky changes.
- If a proposed approach works but an obvious standard or best-practice variant is clearly better, point it out before implementing — unless the user explicitly asked for direct execution.

## Project context

- Read `TODO.md` before making any content or technical changes.
- Treat `TODO.md` as the current feature, architecture, and planning document for this project.
- If requirements or decisions diverge from `TODO.md`, update `TODO.md` accordingly.
- Do not introduce major architectural decisions without aligning them with `TODO.md`.

## Working style

- Keep changes small and traceable.
- Prefer existing project decisions over new abstractions.
- Security-sensitive features must be implemented with clear allowlists, path validation, and least privilege.

## Beads Issue Tracker

Use Beads (`bd`) for all shared task tracking in this repository.

- Do not use markdown TODO lists for shared project work.
- Do not create ad hoc memory files for project tracking. Use `bd remember`!

