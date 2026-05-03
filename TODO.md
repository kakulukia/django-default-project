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

- [ ] `manage.py check --deploy` für Production-Settings grün bekommen.
  - Befund: Warnungen zu HSTS, SSL redirect, secure cookies und schwachem lokalen `SECRET_KEY`.
  - Ziel: `DJANGO_SETTINGS_MODULE=settings python manage.py check --deploy` ohne Warnungen.
  - Rest: HSTS-Subdomains/Preload sind bewusst aus, bis alle Subdomains HTTPS-only sind; lokaler `SECRET_KEY` ist noch schwach.

- [ ] User-API absichern oder entfernen.
  - Befund: `UserViewSet` ist ein voller `ModelViewSet`; Safe-Reads sind in `IsOwnerOrSuperAdmin` immer erlaubt.
  - Risiko: Jeder eingeloggte User kann User-Liste und E-Mail-Adressen lesen.
  - Ziel: Queryset auf `request.user` begrenzen, Admin-only machen oder Demo-API aus dem Template entfernen.

## P1 - hohe Priorität

- [x] `icecream` in `settings/common.py` bewusst behalten.
  - Befund: `icecream` wird auch in Production gelegentlich für Debug-Ausgaben gebraucht.
  - Ziel: Als Runtime-Dependency behalten und global in Common-Settings installieren.

- [ ] django-axes Setting aktualisieren.
  - Befund: `AXES_LOGIN_FAILURE_LIMIT = 2` greift bei django-axes 8 vermutlich nicht.
  - Ziel: `AXES_FAILURE_LIMIT = 2` setzen und Lockout-Verhalten testen.

- [ ] `.idea` aus Git entfernen.
  - Befund: `.idea` ist in `.gitignore`, aber bereits getrackt.
  - Ziel: IDE-State aus dem Template entfernen; nur projektneutrale Dateien behalten, falls wirklich nötig.

- [ ] `TIME_ZONE` korrigieren.
  - Befund: `TIME_ZONE = "CET"` ignoriert Sommerzeit.
  - Ziel: `TIME_ZONE = "Europe/Berlin"`.

- [ ] Whitenoise-Konfiguration bereinigen.
  - Befund: `WhiteNoiseMiddleware` ist gesetzt und `wsgi.py` wrapped zusätzlich manuell mit `WhiteNoise`.
  - Ziel: Eine klare Variante verwenden, bevorzugt Middleware plus passende `STORAGES`.

- [ ] Static-Files-Storage modernisieren.
  - Befund: Kein explizites `STORAGES`/Manifest-Storage für Production.
  - Ziel: `whitenoise.storage.CompressedManifestStaticFilesStorage` für Production prüfen.

- [x] `DEFAULT_FROM_EMAIL` setzen.
  - Befund: `users.models.User.email_user()` nutzt `settings.DEFAULT_FROM_EMAIL`, im Projekt ist es nicht explizit gesetzt.
  - Ziel: Sinnvollen Default in Settings hinterlegen.

- [ ] `base_url` in E-Mails HTTPS-fähig machen.
  - Befund: `email_user()` baut `http://{Site.objects.get_current()}` hart zusammen.
  - Ziel: konfigurierbares `BASE_URL` verwenden.

- [ ] README auf aktuellen Stand bringen.
  - Befund: Django-4-Text, Vue-2-Link, Poetry/uv-Mix, uWSGI/Gunicorn-Widerspruch.
  - Ziel: Doku muss exakt dem Template entsprechen.

## P2 - mittlere Priorität

- [ ] Poetry-Setup kurzfristig konsistent halten.
  - Befund: `pyproject.toml` nutzt Poetry, `.envrc` erstellt aber nur `uv venv`.
  - Ziel: Im aktuellen Branch Poetry als Quelle beibehalten und README/Setup-Befehle darauf abstimmen.

- [ ] `uv`-Migration separat evaluieren.
  - Befund: `uv` waere fuer dieses Template interessant, sollte aber nicht nebenbei in den Fehlerfix-Branch.
  - Ziel: Separater Branch/Spike mit `uv.lock`, `[tool.uv] package = false`, Dependency-Groups, aktualisierter `.envrc` und angepasster README/Deployment-Doku.

- [ ] `pyproject.toml` auf moderne PEP-621-Metadaten prüfen.
  - Befund: `poetry check` warnt, dass mehrere `[tool.poetry]` Felder deprecated sind.
  - Ziel: `[project]` verwenden oder bewusst bei alter Poetry-Struktur bleiben.

- [ ] `django-upgrade` Zielversion aktualisieren.
  - Befund: Pre-commit nutzt `--target-version 5.1`, Projekt dependency ist Django 5.2.
  - Ziel: Target auf 5.2 setzen.

- [ ] Tests ergänzen.
  - Befund: `manage.py test` findet 0 Tests.
  - Ziel: Smoke-Tests fuer Settings, URLs, Admin, API-Auth, ASGI/WSGI und Deployment-Check.

- [ ] Custom User vereinfachen prüfen.
  - Befund: `AbstractBaseUser` ist mehr Wartungsfläche als nötig.
  - Ziel: Wenn keine harte Abweichung nötig ist, auf `AbstractUser` wechseln.

- [ ] Admin fuer Custom User vervollständigen.
  - Befund: `UserAdmin` wird fast unverändert geerbt, aber das Model ist kein `AbstractUser`.
  - Ziel: `fieldsets`, `add_fieldsets`, `list_display`, `search_fields`, `ordering` explizit prüfen.

- [ ] `DEFAULT_AUTO_FIELD` überdenken.
  - Befund: `AutoField` ist bewusst legacy.
  - Ziel: Bei neuen Projekten eher `BigAutoField`, falls keine Altlasten dagegen sprechen.

- [ ] SQLite-Defaults entschärfen oder dokumentieren.
  - Befund: Mehrere PRAGMAs sind template-weit aktiv; `auto_vacuum` ist doppelt/widersprüchlich gesetzt.
  - Ziel: Minimalen SQLite-Default wählen oder klar dokumentieren, wann Postgres Pflicht wird.

- [ ] Dummy-Cache für django-axes prüfen.
  - Befund: `axes_cache` nutzt `DummyCache`; Lockout-Zustand hängt dadurch nicht am Cache.
  - Ziel: Absicht dokumentieren oder stabilen Cache/DB-Handler konfigurieren.

- [ ] Demo-App optional machen.
  - Befund: `sample_app`, Chuck-Norris-API und Vue-Demo landen direkt in neuen Projekten.
  - Ziel: Entweder als klarer Beispielordner oder nach Projektstart leicht entfernbar.

## P3 - Nice-to-have / Cleanup

- [ ] `v-html` in Notifications vermeiden.
  - Befund: `templates/base.pug` rendert Notification-Message als HTML.
  - Ziel: Standardmäßig Text rendern; HTML nur explizit sanitized erlauben.

- [ ] Externe Requests im Default-Template entfernen.
  - Befund: Google Font und Chuck-Norris-API werden im Beispiel genutzt.
  - Ziel: Keine externen Requests im Default-Screen.

- [ ] Moment.js ersetzen oder entfernen.
  - Befund: Moment ist groß und legacy.
  - Ziel: Native `Intl.DateTimeFormat`, `dayjs` oder gar keine Date-Library.

- [ ] Vendored Frontend-Assets aktualisierbar machen.
  - Befund: Vue, Vuetify, Axios, Pinia liegen als statische Dateien im Repo.
  - Ziel: Update-Prozess dokumentieren oder Assets über Build/Download-Script verwalten.

- [ ] `document.querySelector('.stage')` robust machen.
  - Befund: Code kann crashen, wenn `.stage` nicht existiert.
  - Ziel: Null-Check oder Stage-Hinweis aus Template entfernen.

- [ ] `href="#"` bei Buttons entfernen.
  - Befund: Demo-Button nutzt Link-Verhalten für eine Aktion.
  - Ziel: Button ohne Link-Href.

- [ ] Texte und Kommentare bereinigen.
  - Befund: Alte Django-Versionen, Tippfehler, gemischte deutsche/englische Kommentare.
  - Ziel: Kurze, aktuelle, template-taugliche Kommentare.

- [ ] `fabfile.py` kritisch prüfen.
  - Befund: Fabric-Deployment enthält harte Namen, PM2, Poetry und destruktives lokales DB-Ersetzen.
  - Ziel: Entweder modernisieren oder als optionales Beispiel auslagern.

- [ ] `get_new_db()` absichern.
  - Befund: Entfernt lokal `db.sqlite3` ohne Sicherheitsabfrage.
  - Ziel: Backup/Bestätigung einbauen oder Task entfernen.

- [x] `settings/deployment/project.yml` korrigieren oder entfernen.
  - Befund: `vaccum` ist falsch geschrieben; Socket-Rechte `666` sind fragwürdig.
  - Ziel: Nur behalten, wenn uWSGI wirklich Ziel-Stack ist.
  - Ergebnis: Entfernt, weil Gunicorn der Ziel-Stack ist.

- [ ] `.gitignore` erweitern.
  - Befund: `__pycache__`, `.ruff_cache`, Coverage-Dateien und lokale Secrets/Caches sollten expliziter ignoriert werden.
  - Ziel: Template-taugliche Python/Django-Gitignore-Regeln.

## Bereits geprüft

- `python manage.py check`: ok.
- `python manage.py test`: ok, aber 0 Tests.
- `ruff check .`: ok.
- `ruff format --check .`: ok.
- `python manage.py check --deploy`: HSTS-Subdomains/Preload-Warnungen und lokale `SECRET_KEY`-Warnung bleiben bewusst offen.
- `poetry check`: ok, nur Deprecation-Warnungen zu `[tool.poetry]`-Metadaten.
