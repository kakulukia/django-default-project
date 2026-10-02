# Django default project

This repository maintains a runnable Django project and a Cookiecutter variant.

- `main`: develop and update the application in `project/`.
- `feature/cookiecutter`: generate projects from `{{ cookiecutter.project_slug }}/`.

Both branches share the generator configuration, hooks, tests, quality
configuration and update script in the repository root. The template branch
only renames the application directory and adds project metadata placeholders.

## Develop and update the application

Run application commands inside `project/`:

```bash
cd project
uv sync --locked
export DJANGO_SETTINGS_MODULE=settings.andy
uv run python manage.py runserver
```

Update dependencies with the existing application script:

```bash
./scripts/uv-update
```

Review and test the application changes, then commit them on `main` before
updating the template branch. Application setup and deployment instructions
are in the README inside the application directory.

The application's `.envrc` activates its own `project/.venv`. When using
direnv, allow this file from `project/`. A virtual environment left in the
repository root belongs to the previous layout.

## Update the template branch

From the repository root, after reviewing and committing changes on `main`:

```bash
./update-cookiecutter
```

The script requires local `main` and `feature/cookiecutter` branches, a clean
working tree including untracked files, uv and Sass. It rebases the template
branch onto local `main` and runs the template tests with Cookiecutter 2.7.1
and Python 3.14. After successful validation it returns to the starting branch.

The merge backend detects the application directory rename. The script enables
directory rename handling for this rebase so new files added in `project/`
also move into `{{ cookiecutter.project_slug }}/`. Review the resulting diff,
especially changed project metadata and new files that need placeholders or
must be copied without rendering.

A rebase conflict stops before validation. Resolve the conflicts and run
`git rebase --continue`, or use `git rebase --abort`, then rerun the script.
A validation failure leaves the template branch checked out for inspection.

Rebasing changes template commit IDs. Publishing is a separate step: review
the branch before using an explicitly scoped `git push --force-with-lease`.

## Generate a project

Use the published template branch explicitly:

```bash
uvx --from 'cookiecutter==2.7.1' cookiecutter \
  gh:kakulukia/django-default-project --checkout feature/cookiecutter
```

Cookiecutter asks for a project title, slug, description, author name and email,
and an optional repository URL. The slug must start with a lowercase letter
and use lowercase letters, digits and single hyphens, such as `customer-portal`.
New projects start at version `0.1.0` and inherit MIT license metadata.

The author's first name determines a personal settings file: `Alex Example`
creates `settings/alex.py`, importing `settings.dev`. Names are normalized;
reserved module names get a `_local` suffix. The generated README shows the
resulting settings module and contains setup and deployment instructions.

Publish the template branch before using this GitHub command. To check a local
checkout of `feature/cookiecutter` without publishing:

```bash
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

The generator tests run on `feature/cookiecutter`, where the template directory
exists. They generate projects, check the locked dependencies, run the Django
tests and validate the generated code:

```bash
uv run --no-project --python 3.14 --with 'cookiecutter==2.7.1' python tests/test_template.py
```
