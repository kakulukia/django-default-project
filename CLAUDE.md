# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Kommunikation

- Antworte direkt und kompakt. Keine Höflichkeitsfloskeln, keine Wiederholung der Frage.
- Widersprich aktiv, wenn Annahmen riskant, falsch oder unvollständig sind.
- Stelle bei fachlichen Einwänden Rückfragen, bevor du riskante Änderungen umsetzt.
- Weise auf naheliegende Best-Practice-Varianten hin und frage nach, sofern nicht explizit direktes Umsetzen verlangt wurde.

## Workflow

- Lies `TODO.md` vor inhaltlichen oder technischen Änderungen. Es ist die aktuelle Feature-, Architektur- und Planungsdatei.
- Wenn Anforderungen oder Entscheidungen von `TODO.md` abweichen, aktualisiere `TODO.md` mit.
- Keine größeren Architekturentscheidungen ohne Abgleich mit `TODO.md`.
- Halte Änderungen klein und nachvollziehbar.
- Bevorzuge vorhandene Projektentscheidungen gegenüber neuen Abstraktionen.
- Sicherheitsrelevante Funktionen mit klaren Allowlists, Pfadvalidierung und minimalen Rechten umsetzen.

## Commands

```bash
# Development server (personal settings module required — see Settings below)
DJANGO_SETTINGS_MODULE=settings.andy python manage.py runserver

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
- `andy.py` — per-developer example: `cp settings/andy.py settings/<yourname>.py`, then set `DJANGO_SETTINGS_MODULE=settings.<yourname>`. Never commit personal modules.

`manage.py` defaults to `DJANGO_SETTINGS_MODULE=settings` (production). Always export a dev module when running locally.

## App architecture

**`utils/`** — shared base. `BaseModel` (abstract) provides `created`/`modified` timestamps and a default `ordering = ["-created"]`. Use `.data` (not `.objects`) as the canonical manager — all models inherit this.

**`users/`** — custom auth. `User` extends `AbstractBaseUser` + `BaseModel` + `PermissionsMixin`. `email_user(template_name, context, request)` sends via `post_office` using the request-aware scheme + Site domain; activates the German locale (`de-de`).

**`sample_app/`** — demo only (Chuck Norris jokes, Vue 3 + Vuetify). Intended to be replaced or removed in real projects.

URL routing is **centralized** in `settings/urls.py` — there are no per-app `urls.py` files.

## DRF permissions

`utils.IsOwnerOrSuperAdmin` has a class-name → owner-attribute mapping:

```python
owner_mapping = {"User": "self", ...}
```

When adding a new model to the API, add an entry here. `UserViewSet.get_queryset` restricts non-staff to their own row; staff see all rows. This is the intended pattern for new viewsets.

## Templates & frontend

Templates use **Pug** via `pypugjs`. The base template (`templates/base.pug`) loads Vue 3, Vuetify, Axios, Pinia, and Moment.js from vendored files in `assets/js/vendor/`.

## Key dependencies and conventions

- **Secrets**: managed by `django-secrets`; stored in `my_secrets/secrets.py`. `manage.py` calls `django_secrets.startup.check()` before startup.
- **Email**: `post_office` backend with `post_office.cron.send_queued_mail` flushed every minute via kronos (`utils/cron.py`).
- **Background tasks**: `django_tasks` with the database backend (`utils/tasks.py`).
- **Login-as**: `loginas` (only superusers, never superuser-to-superuser); `UserAdmin` uses the loginas change form template.
- **Brute-force protection**: `django-axes` with `AXES_FAILURE_LIMIT = 2`; `axes_cache` is intentionally `DummyCache` (lockout state lives in the DB, not cache).
- **`ic()`** is globally available in all environments (icecream installed in `common.py`).
- **Language**: `de-de`, **Timezone**: `Europe/Berlin`.
- **Line length**: 120 (ruff). Imports sorted with `I001`.

## Open work (from TODO.md)

Notable open items that affect day-to-day work:

- P2: Migrate from Poetry to `uv` — `uv.lock`, PEP-621 `[project]` metadata, updated `.envrc`, README and deployment docs.
- P2: Integrate Sentry — `SENTRY_DSN` secret, `sentry_sdk.init()` in `settings/common.py` guarded by DSN presence.
- P2: `django-upgrade` pre-commit target is `5.1`; project runs Django 5.2 — bump when convenient.
- P2: `DEFAULT_AUTO_FIELD` is legacy `AutoField`; new projects should prefer `BigAutoField`.
- P2: SQLite PRAGMAs in `common.py` include a duplicate/conflicting `auto_vacuum` setting.
- P2: `UserAdmin` fieldsets not fully customized for the `AbstractBaseUser`-based model.
- P3: `v-html` in `base.pug` notifications is an XSS risk — sanitize before rendering HTML there.
