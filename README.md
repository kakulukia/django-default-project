# django-default-project

A Cookiecutter template for Django projects with uv, Django REST Framework,
Django Tasks, PUG/Sass/Vue, and Fabric/PM2 deployment support.

## Create a project

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
uvx --from 'cookiecutter==2.7.1' cookiecutter gh:kakulukia/django-default-project
```

This command uses the published GitHub version. Local changes are only available
when generating from your checkout, as described under **Work on the template**.
The GitHub command requires the Cookiecutter conversion to have been published.

Cookiecutter asks for the project title, a directory/package name (`project_slug`),
a description, author name and email, and an optional repository URL. The slug
must start with a lowercase letter and use lowercase letters, digits and single
hyphens, for example `customer-portal`. New projects start at version `0.1.0`.

The generated README contains the local setup and deployment instructions.
Domain, server and production settings are configured later in that project.
The MIT license metadata is inherited; review it for your own project.

This replaces the former `django-admin startproject --template=…` workflow.
Existing projects are unaffected; Cookiecutter creates new projects only.

## Work on the template

The application source lives in `{{ cookiecutter.project_slug }}/`. Edit it there,
then run this command from the template repository to generate a disposable
project for running Django or testing dependency updates:

```bash
uvx --from 'cookiecutter==2.7.1' cookiecutter . --output-dir /tmp
```

When running from another directory, replace `.` with the path to your local
template repository. This also includes changes that have not been committed.

Choose a fresh project name for each working copy. Follow its generated README
to install dependencies and start Django. Keep secrets, databases, virtual
environments and generated assets in the working copy, outside the template.
The source file `{{ '.envrc' }}` becomes `.envrc` only in the generated project,
so direnv does not initialize an environment inside the raw template.

Only the project directory is copied. This README, generation hooks, tests and
local Beads/Graphify data stay outside new projects. General ignore rules and
optional tool configuration are included so new projects can initialize their
own tools. `assets/`, `templates/` and `scripts/` are copied byte-for-byte using
Cookiecutter's `_copy_without_render` setting; Django, PUG and Vue syntax is not
processed by Cookiecutter.

Project metadata is rendered in `pyproject.toml` and `uv.lock`. When updating
dependencies with the generated project's `scripts/uv-update`, bring the changed
dependency pins and lockfile back to the template, keeping the templated package
name and version `0.1.0`. Do not copy its secrets or runtime files back.

## Validate changes

With uv and Sass (`npm install -g sass`) available, run:

```bash
uv run --no-project --python 3.14 --with 'cookiecutter==2.7.1' python tests/test_template.py
```

The test generates projects in a temporary directory, verifies metadata, optional
URLs, unchanged frontend files, executable scripts and input validation, then
installs the locked dependencies and runs the generated project's Django tests
and Ruff checks. It supplies temporary test secrets and removes the generated
projects afterward. It does not initialize Git, commit or deploy anything.

The root pre-commit configuration checks generator files. Raw Jinja templates
are excluded; the generated project retains its full pre-commit configuration.
