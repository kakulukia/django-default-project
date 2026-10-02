# Django default project

This repository publishes a Cookiecutter template on its default branch and
maintains a runnable Django project on a separate development branch.

- `main`: generate projects from `{{ cookiecutter.project_slug }}/`.
- `dev`: develop and update the application in `project/`.

Both branches share the generator configuration, hooks, tests, quality
configuration and update script in the repository root. The template branch
only renames the application directory and adds project metadata placeholders.

## Develop and update the application

Switch to the development branch, then run application commands inside `project/`:

```bash
git switch dev
cd project
uv sync --locked
export DJANGO_SETTINGS_MODULE=settings.andy
uv run python manage.py runserver
```

Update dependencies with the existing application script:

```bash
./scripts/uv-update
```

Review and test the application changes, then commit them on
`dev` before updating the template branch. Application setup
and deployment instructions are in the README inside the application directory.

The application's `.envrc` activates its own `project/.venv`. When using
direnv, allow this file from `project/`.

## Update the template branch

From the repository root, after reviewing and committing changes on
`dev`:

```bash
git fetch origin
git log --oneline main..origin/main
```

Review and integrate any incoming changes to remote `main` before continuing:

```bash
./update-cookiecutter
git diff dev main
```

The script requires local `main` and `dev` branches, a clean
working tree including untracked files, uv and Sass. It rebases the template
branch `main` onto local `dev` and runs the template tests with
Cookiecutter 2.7.1 and Python 3.14. After successful validation it returns to the
starting branch.

The merge backend detects the application directory rename. The script enables
directory rename handling for this rebase so new files added in `project/`
also move into `{{ cookiecutter.project_slug }}/`. Review the resulting diff,
especially changed project metadata and new files that need placeholders or
must be copied without rendering.

A rebase conflict stops before validation. Resolve the conflicts and run
`git rebase --continue`, or use `git rebase --abort`, then rerun the script.
A validation failure leaves the template branch checked out for inspection.

Rebasing keeps the template changes as separate commits and changes their IDs.
Overlapping edits can still cause conflicts that need manual resolution.

Publishing is a separate step. Before rebasing, the script records the current
local `origin/main` tracking ref. After successful validation it prints a
`git push --force-with-lease=refs/heads/main:<expected-commit> origin main`
command with that exact commit ID. After reviewing the diff, use that printed
command to publish `main`. The push is rejected if remote `main` has changed
since the recorded commit, even if a background fetch has updated `origin/main`.
The script does not push either branch.

Publish the application branch separately with a normal push:

```bash
git push --set-upstream origin dev
```

## Generate a project

Cookiecutter uses the published default branch `main`:

```bash
cookiecutter gh:kakulukia/django-default-project
```

Cookiecutter asks for a project title, slug, description, author name and email,
and an optional repository URL. The slug must start with a lowercase letter
and use lowercase letters, digits and single hyphens, such as `customer-portal`.
New projects start at version `0.1.0` and inherit MIT license metadata.

The author's first name determines a personal settings file: `Alex Example`
creates `settings/alex.py`, importing `settings.dev`. Names are normalized;
reserved module names get a `_local` suffix. The generated README shows the
resulting settings module and contains setup and deployment instructions.

Publish `main` before using this GitHub command. To check a local checkout of
`main` without publishing:

```bash
git switch main
uvx --from 'cookiecutter==2.7.1' cookiecutter . --output-dir /tmp/generated-projects
```

Only the application directory is generated. Repository maintenance files and
local Beads/Graphify data stay outside new projects. General ignore rules and
optional tool configuration are included. `assets/`, `templates/` and `scripts/`
are copied without rendering to preserve Django, PUG, Vue and shell syntax.
The template's `{{ '.envrc' }}` filename becomes `.envrc` only after generation,
so direnv does not initialize an environment inside the raw template.

## Check the maintenance workflow

The Git workflow tests run on either branch:

```bash
python3 tests/test_update_cookiecutter.py
```

The generator tests run on `main`, where the template directory exists. They
generate projects, check the locked dependencies, run the Django tests and
validate the generated code:

```bash
uv run --no-project --python 3.14 --with 'cookiecutter==2.7.1' python tests/test_template.py
```
