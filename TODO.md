# TODO

- [ ] `templates/base.pug` entschlacken und den Frontend-Bootstrap in eine echte JS-Entry-Datei auslagern
- [ ] `assets/js/BaseApp.js` refactoren: kein globales Mixin mit dynamischem `this[action]()`-Dispatch, Notification-Handling und API-Fehler zentraler kapseln
- [ ] `settings/common.py` besser in `base`/`dev`/`prod` trennen und Hostname-, Mail- und DB-Details stärker über Environment/Secrets ziehen
- [ ] `TODO.md` als echten Template-Contract ausformulieren statt als Platzhalter zu lassen
