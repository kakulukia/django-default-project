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

- Use Beads (`bd`) as the current feature, architecture, and planning source.
- Run `bd prime` when Beads context is missing or stale.
- If requirements or decisions need durable tracking, create or update a Bead.
- Do not introduce major architectural decisions without recording them in Beads.

## Working style

- Keep changes small and traceable. 
- Generally work minimal/YAGNI style.
- Prefer existing project decisions over new abstractions.
- Security-sensitive features must be implemented with clear allowlists, path validation, and least privilege.

## Beads Issue Tracker

Use Beads (`bd`) for all shared task tracking in this repository.

- Do not use markdown TODO lists for shared project work.
- Do not create ad hoc memory files for project tracking; use `bd remember`.
