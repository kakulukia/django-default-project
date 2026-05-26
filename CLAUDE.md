# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication

- Reply directly and concisely. No pleasantries, no restating the question.
- Push back actively when assumptions are risky, wrong, or incomplete.
- Ask clarifying questions on technical objections before implementing risky changes.
- Point out obvious best-practice alternatives and ask before implementing — unless direct execution was explicitly requested.

## Workflow

- Read `TODO.md` before making any content or technical changes. It is the current feature, architecture, and planning document.
- If requirements or decisions diverge from `TODO.md`, update `TODO.md` accordingly.
- No major architectural decisions without aligning with `TODO.md`.
- Keep changes small and traceable.
- Prefer existing project decisions over new abstractions.
- Implement security-sensitive features with clear allowlists, path validation, and least privilege.

## Commands

```bash
# Development server (personal settings module required — see Settings below)
DJANGO_SETTINGS_MODULE=settings.andy python manage.py runserver --nostatic

# Tests
python manage.py test                        # all tests
python manage.py test users.tests            # single module
python manage.py test users.tests.UserViewSetTest.test_me  # single test

# Lint / format
ruff check .
ruff format .

# Migrations
python manage.py makemigrations
python manage.py migrate

# Static assets (production pipeline)
python manage.py compress -e pug,html --force
python manage.py collectstatic --noinput

# Cron tasks (kronos)
python manage.py installtasks

# Deploy (Fabric)
fab deploy     # push deps + static + restart
fab migrate    # install deps + migrate + restart
```

## Settings structure

`settings/` is a flat package (no nested project module):

- `common.py` — production baseline (`DEBUG=False`, SSL on, HSTS 3600 s). This is the default module.
- `dev.py` — imports common, flips `DEBUG=True`, disables SSL/HSTS, adds debug toolbar + browser reload.
- `andy.py` — per-developer example: `cp settings/andy.py settings/<yourname>.py`, then set `DJANGO_SETTINGS_MODULE=settings.<yourname>`.

`manage.py` defaults to `DJANGO_SETTINGS_MODULE=settings` (production). Always export a dev module when running locally.

## App architecture

**`utils/`** — shared base. `BaseModel` (abstract) provides `created`/`modified` timestamps and a default `ordering = ["-created"]`. Use `.data` (not `.objects`) as the canonical manager — all models inherit this.

**`users/`** — custom auth. `User` extends `AbstractUser` + `BaseModel`. `email_user(template_name, context)` sends via `post_office` using `SECURE_SSL_REDIRECT` to determine the URL scheme + the current Site domain; activates the German locale (`de-de`).

URL routing is **centralized** in `settings/urls.py` — there are no per-app `urls.py` files.

## DRF permissions

`utils.IsOwnerOrSuperAdmin` has a class-name → owner-attribute mapping:

```python
owner_mapping = {"User": "self", ...}
```

When adding a new model to the API, add an entry here. `UserViewSet.get_queryset` restricts non-staff to their own row; staff see all rows. `UserViewSet.get_permissions` restricts `create` to staff (`IsAdminUser`). This is the intended pattern for new viewsets.

## Templates & frontend

Templates use **Pug** via `pypugjs`. The base template (`templates/base.pug`) loads Vue 3, Vuetify, Axios, Pinia, and Moment.js from vendored files in `assets/js/vendor/`. The `lang` attribute on `<html>` is driven by `{{ LANGUAGE_CODE }}` from the `i18n` context processor.

## Key dependencies and conventions

- **Secrets**: managed by `django-secrets`; stored in `my_secrets/secrets.py`. `manage.py` calls `django_secrets.startup.check()` before startup.
- **Email**: `post_office` backend with `post_office.cron.send_queued_mail` flushed every minute via kronos (`utils/cron.py`).
- **Background tasks**: `django_tasks` with the database backend (`utils/tasks.py`).
- **Login-as**: `loginas` (only superusers, never superuser-to-superuser); `UserAdmin` uses the loginas change form template.
- **Brute-force protection**: `django-axes` with `AXES_FAILURE_LIMIT = 2`; `axes_cache` is intentionally `DummyCache` (lockout state lives in the DB, not cache).
- **`ic()`** is globally available in all environments (icecream installed in `common.py`).
- **Language**: `de-de`, **Timezone**: `Europe/Berlin`.
- **Line length**: 120 (ruff). Imports sorted with `I001`.

## New project checklist

When creating a new project from this template:

- `settings/common.py`: set `ALLOWED_HOSTS`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`.
- `settings/deployment/`: update `APP_NAME` in `project.sh` and `fabfile.py`.
- `my_secrets/definitions.py`: check which secrets are needed (`SENTRY_DSN` etc.).
- `LANGUAGE_CODE` / `TIME_ZONE` in `common.py`: adjust for the target locale.
- Remove the `UserChange` demo component from `base.pug` / `index.pug` if not needed.


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
