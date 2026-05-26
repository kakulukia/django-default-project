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

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:7510c1e2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
