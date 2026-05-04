# TODO

## P0 - muss vor Template-Nutzung passieren

- [x] `poetry.lock` reparieren.
  - Befund: `poetry check` meldete, dass `pyproject.toml` deutlich vom Lockfile abweicht.
  - Ergebnis: `poetry check` läuft wieder mit Exit-Code 0 durch.
  - Rest: Es bleiben nur Deprecation-Warnungen zur alten `[tool.poetry]`-Metadatenform.

- [x] ASGI-Settings korrigieren.
  - Befund: `settings/asgi.py` referenziert `testerei.settings`.
  - Ziel: Default auf das echte Settings-Modul setzen, z. B. `settings`.

- [x] Deployment-Setup vereinheitlichen.
  - Befund: README beschreibt uWSGI, `project.sh` nutzt Gunicorn, Nginx nutzt `uwsgi_pass`.
  - Ziel: Gunicorn + PM2 + Nginx `proxy_pass`; kein systemd.

- [x] Pfad in `settings/deployment/project.sh` korrigieren.
  - Befund: `.venv` wird relativ zu `settings/deployment` gesucht und liegt dadurch vermutlich falsch.
  - Ziel: Projektroot sauber bestimmen und `.venv/bin/gunicorn` dort aufrufen.

- [x] Production-Settings ergänzen.
  - Befund: `settings/common.py` ist die Production-Baseline, war aber nicht so dokumentiert.
  - Ziel: `common.py` als Default-Production-Settings dokumentieren und HTTPS-/Cookie-Security dort explizit setzen.

- [x] Deploy-Check-Warnungen klassifizieren statt blind grün machen.
  - Befund: Verbleibende Warnungen sind HSTS-Subdomains, HSTS-Preload und lokaler schwacher `SECRET_KEY`.
  - Ergebnis: HSTS-Subdomains/Preload bleiben sichere Template-Defaults und sind in README/common dokumentiert.

- [x] `django-secrets` SECRET_KEY-Abfrage upstream verbessern.
  - Befund: `manage.py` fragt fehlende Secrets interaktiv ab; bei `SECRET_KEY` wird lokal schnell ein schwacher Wert eingegeben.
  - Ziel: Im `django-secrets` Paket fuer `SECRET_KEY` automatisch einen starken Django-Key vorschlagen und per Enter uebernehmen lassen.
  - Nicht im Template loesen; das Verhalten gehoert in `django_secrets.startup.check()`.
  - Ergebnis: Auf `django-secrets` 3.0.3 aktualisiert; `SECRET_KEY` wurde damit neu erzeugt und sauber gezogen.

- [x] HSTS-Subdomains/Preload pro Projekt entscheiden.
  - Befund: `SECURE_HSTS_INCLUDE_SUBDOMAINS` und `SECURE_HSTS_PRELOAD` sollten nicht pauschal im Template aktiviert werden.
  - Ziel: In echten Projekten auf `True` setzen, sobald alle betroffenen Subdomains HTTPS-only und preload-ready sind.

- [x] User-API absichern oder entfernen.
  - Befund: `UserViewSet` ist ein voller `ModelViewSet`; Safe-Reads sind in `IsOwnerOrSuperAdmin` immer erlaubt.
  - Risiko: Jeder eingeloggte User kann User-Liste und E-Mail-Adressen lesen.
  - Ziel: Queryset auf `request.user` begrenzen, Admin-only machen oder Demo-API aus dem Template entfernen.
  - Ergebnis: Nicht-Staff sieht nur sich selbst; Staff sieht alle User.

## P1 - hohe Priorität

- [x] `icecream` in `settings/common.py` bewusst behalten.
  - Befund: `icecream` wird auch in Production gelegentlich für Debug-Ausgaben gebraucht.
  - Ziel: Als Runtime-Dependency behalten und global in Common-Settings installieren.

- [x] django-axes Setting aktualisieren.
  - Befund: `AXES_LOGIN_FAILURE_LIMIT = 2` greift bei django-axes 8 vermutlich nicht.
  - Ziel: `AXES_FAILURE_LIMIT = 2` setzen und Lockout-Verhalten testen.

- [x] `.idea` aus Git entfernen.
  - Befund: `.idea` ist in `.gitignore`, aber bereits getrackt.
  - Ziel: IDE-State aus dem Template entfernen; nur projektneutrale Dateien behalten, falls wirklich nötig.
  - Ergebnis: `.idea` ist nicht mehr getrackt und bleibt per `.gitignore` ignoriert.

- [x] `TIME_ZONE` korrigieren.
  - Befund: `TIME_ZONE = "CET"` ignoriert Sommerzeit.
  - Ziel: `TIME_ZONE = "Europe/Berlin"`.

- [x] Whitenoise-Konfiguration bereinigen.
  - Befund: `WhiteNoiseMiddleware` ist gesetzt und `wsgi.py` wrapped zusätzlich manuell mit `WhiteNoise`.
  - Ziel: Eine klare Variante verwenden, bevorzugt Middleware plus passende `STORAGES`.
  - Ergebnis: WSGI-Wrapping entfernt; `WhiteNoiseMiddleware` bleibt die einzige Integration.

- [x] Static-Files-Storage modernisieren.
  - Befund: Kein explizites `STORAGES`/Manifest-Storage für Production.
  - Ziel: `whitenoise.storage.CompressedManifestStaticFilesStorage` für Production prüfen.
  - Ergebnis: `STORAGES["staticfiles"]` nutzt Whitenoise `CompressedManifestStaticFilesStorage`.
  - Verifiziert: `compress` -> `collectstatic` läuft; fehlende Sourcemap-/Font-Referenzen in vendored Assets wurden bereinigt.

- [x] `DEFAULT_FROM_EMAIL` setzen.
  - Befund: `users.models.User.email_user()` nutzt `settings.DEFAULT_FROM_EMAIL`, im Projekt ist es nicht explizit gesetzt.
  - Ziel: Sinnvollen Default in Settings hinterlegen.

- [x] `base_url` in E-Mails HTTPS-fähig machen.
  - Befund: `email_user()` baut `http://{Site.objects.get_current()}` hart zusammen.
  - Ziel: konfigurierbares `BASE_URL` verwenden.
  - Ergebnis: `email_user()` nutzt jetzt `Site + scheme`.

- [x] README auf aktuellen Stand bringen.
  - Befund: Django-4-Text, Vue-2-Link, Poetry/uv-Mix, uWSGI/Gunicorn-Widerspruch.
  - Ziel: Doku muss exakt dem Template entsprechen.

## P2 - mittlere Priorität

- [x] Auf `uv` migrieren.
  - Ergebnis: `pyproject.toml` auf PEP-621 (`[project]` + `[dependency-groups]`), `[tool.uv] package = false`, `uv.lock` erzeugt, `poetry.lock` entfernt, `.envrc` und `fabfile.py` angepasst, README und Deployment-Doku aktualisiert. `toml`-Dev-Dep entfernt.

- [x] Sentry in Template integrieren.
  - Ergebnis: `sentry_sdk.init()` in `settings/common.py` aktiv, greift nur wenn `SENTRY_DSN` in `my_secrets/secrets.py` gesetzt ist. Hinweis und Kommentar in `definitions.py` und README ergänzt.

- [x] `pyproject.toml` auf moderne PEP-621-Metadaten prüfen.
  - Ergebnis: Im Zuge der uv-Migration auf `[project]` + `[dependency-groups]` umgestellt.

- [x] `django-upgrade` Zielversion aktualisieren.
  - Ergebnis: Target läuft auf `6.0` (zusammen mit Django-6-Upgrade angepasst).

- [x] Tests ergänzen.
  - Ergebnis: 12 Tests. Neu in `utils/tests.py`: WSGI/ASGI-Import, Index-200, Admin-Redirect, unauthenticated-API-403.

- [x] Custom User vereinfachen prüfen.
  - Ergebnis: Auf `AbstractUser` umgestellt. Alle redundanten Felddefinitionen und Methoden entfernt. Migration für `first_name`/`last_name` max_length 30→150 und `username`-Validator-Cleanup generiert.

- [x] Admin fuer Custom User vervollständigen.
  - Ergebnis: `readonly_fields` (created, modified, last_login), Timestamps-Fieldset, list_display mit created/is_active, ordering nach -created.

- [x] `DEFAULT_AUTO_FIELD` überdenken.
  - Ergebnis: Auf `BigAutoField` umgestellt. Migration für `users.User` generiert. App-Level-Override in `utils/apps.py` entfernt.

- [x] SQLite-Defaults entschärfen oder dokumentieren.
  - Ergebnis: Doppeltes `auto_vacuum` bereinigt (INCREMENTAL behalten), Kommentar ergänzt dass es nur beim DB-Erstellen greift.

- [x] Dummy-Cache für django-axes prüfen.
  - Ergebnis: DummyCache ist absichtlich — zwingt axes zur DB-basierten Lockout-Verwaltung (restart-sicher). Kommentar ergänzt.

- [x] Demo-App optional machen.
  - Ergebnis: `sample_app` entfernt. Index-View ist jetzt ein `TemplateView` direkt in `settings/urls.py`.

## P3 - Nice-to-have / Cleanup

- [x] `v-html` in Notifications vermeiden.
  - Ergebnis: `v-html` → `v-text` in `base.pug`.

- [ ] Externe Requests im Default-Template entfernen.
  - Befund: Google Font und Chuck-Norris-API werden im Beispiel genutzt.
  - Entscheidung: Demo bleibt bewusst drin — wird nicht umgesetzt.

- [ ] Moment.js ersetzen oder entfernen.
  - Befund: Moment ist groß und legacy.
  - Entscheidung: Wird vorerst nicht angefasst, da Demo darauf aufbaut.

- [ ] Vendored Frontend-Assets aktualisierbar machen.
  - Befund: Vue, Vuetify, Axios, Pinia liegen als statische Dateien im Repo.
  - Ziel: Update-Prozess dokumentieren oder Assets über Build/Download-Script verwalten.

- [x] `document.querySelector('.stage')` robust machen.
  - Ergebnis: Hardcoded Stage-Check entfernt; optional-chaining (`?.`) für `title.focus()` ergänzt.

- [x] `href="#"` bei Buttons entfernen.
  - Ergebnis: `href="#"` aus Demo-Button entfernt.

- [x] Texte und Kommentare bereinigen.
  - Ergebnis: Veraltete Kommentare aktualisiert, Demo-Texte bereinigt.

- [x] `fabfile.py` kritisch prüfen.
  - Ergebnis: Poetry-Referenzen auf uv umgestellt (vorherige Session). Harte Namen und PM2 sind Template-Platzhalter — bleiben mit Kommentar.

- [x] `get_new_db()` absichern.
  - Ergebnis: Bestätigungsabfrage vor destruktivem DB-Ersetzen eingebaut.

- [x] `settings/deployment/project.yml` korrigieren oder entfernen.
  - Ergebnis: Entfernt, weil Gunicorn der Ziel-Stack ist.

- [x] `.gitignore` erweitern.
  - Ergebnis: `__pycache__/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `node_modules/`, `.env`, `media/` ergänzt.

## Bereits geprüft

- `python manage.py check`: ok.
- `python manage.py test`: ok, 12 Tests.
- `ruff check .`: ok.
- `ruff format --check .`: ok.
- `python manage.py check --deploy`: HSTS-Subdomains/Preload-Warnungen und lokale `SECRET_KEY`-Warnung bleiben bewusst offen.
- `uv lock`: ok (Poetry entfernt).
