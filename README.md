# django-default-project

#### Django

This project serves as a base template for new Django projects using
[uv](https://docs.astral.sh/uv/) for dependency management. It comes preconfigured
with a robust set of third-party packages to help you start quickly and maintain best practices.

**Included Packages:**

```toml
[project]
dependencies = [
    "django>=6.0",
    "django-axes",
    "django-compressor",
    "django-extensions",
    "django-kronos",
    "django-loginas",
    "django-post-office",
    "django-secrets",
    "django-tasks",
    "django-tasks-db",
    "djangorestframework",
    "gunicorn",
    "icecream",
    "pendulum",
    "pillow",
    "pypugjs",
    "requests",
    "sentry-sdk",
    "whitenoise",
]

[dependency-groups]
dev = [
    "django-browser-reload",
    "django-debug-toolbar",
    "fab-classic",
    "ipdb",
    "pre-commit",
    "ruff",
]
```

Furthermore, this template includes a Hello World example utilizing PUG templates, SASS styles, and
VueJS. The example even features [Chuck Norris facts](https://api.chucknorris.io) to provide a fun,
interactive experience during development.

#### Frontend

The frontend setup is minimal and designed to add reactivity to your pages without the overhead
of a full single-page application. It includes:

- [Vue 3](https://vuejs.org/guide/introduction.html) – the core JavaScript framework.
- [Vuetify](https://vuetifyjs.com/en/) – a Material Design component framework for Vue.
- [Pinia](https://pinia.vuejs.org/) – state management.
- [Axios](https://github.com/axios/axios) – for AJAX calls.
- [Material Design Icons](https://pictogrammers.com/library/mdi/) – iconography for your UI.

For more complex frontends, consider building a dedicated VueJS application (using `vue ui`) in
conjunction with Django REST Framework. But for smaller projects, this template provides a
lightweight solution that allows you to add interactivity without the need to deal with ~900
node dependencies.

#### Settings Hierarchy

This template features a simplified yet flexible settings hierarchy inspired by best practices
(e.g., *Two Scoops of Django*). The goal is to keep configuration clear and maintainable while
allowing easy customization for different environments or developers:

1. **Base Settings:**
All common configurations are located in a central file (`settings/common.py`). This file contains
settings shared by all environments.

2. **Environment-Specific Overrides:**
Create separate files for environment-specific settings (e.g., `settings/dev.py`,
`settings/stage.py`). Each of these files imports everything from `common.py` and then applies
overrides specific to that environment. `settings/dev.py` is the local development baseline.

3. **Personalized Settings:**
Developers can maintain their own settings (e.g., `settings/alice.py`, `settings/bob.py`) based
on the default environment file. Simply set the environment variable `DJANGO_SETTINGS_MODULE`
to point to your custom settings (e.g., `export DJANGO_SETTINGS_MODULE=settings.alice`).

For production, review and commit the relevant values in `settings/common.py` or in a tracked
environment-specific settings module:

```python
ALLOWED_HOSTS = ["example.com", "www.example.com"]
CSRF_TRUSTED_ORIGINS = ["https://example.com", "https://www.example.com"]
DEFAULT_FROM_EMAIL = "webmaster@example.com"
```

Keep HSTS subdomains/preload disabled in the template. Enable them in a
project-specific production settings module only after every affected
subdomain is HTTPS-only:

```python
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

4. **Secret Management:**
With [django-secrets](https://github.com/jezdez/django-secrets), your sensitive configuration
(like API keys and passwords) is managed separately, ensuring that secrets remain secure and
deployment is streamlined (e.g., in CI/CD pipelines).

This flat yet modular approach minimizes complexity while allowing each project or developer to
tailor the settings as needed without interfering with the shared base configuration.

#### Sentry

[Sentry](https://sentry.io) error reporting is included but disabled by default. On first run,
`manage.py` will prompt for a `SENTRY_DSN` — leave it empty to disable Sentry, or enter your
project DSN to enable it. `sentry_sdk.init()` is called automatically in `settings/common.py`
whenever a non-empty DSN is present.

#### Clean Code

A pre-configured pre-commit hook is included to enforce code quality. Install it with:

```bash
pre-commit install
```

#### Static Files

Static files are served through
[Whitenoise](http://whitenoise.evans.io/en/stable/) via `WhiteNoiseMiddleware`, so Django can
serve collected static files without an additional static-file server for small deployments.
The production static files storage uses hashed filenames, so changed CSS/JS assets get new URLs
and do not rely on browsers noticing changed content behind an old path.

#### fabfile

A ready-to-use `fabfile` is provided to simplify common deployment tasks:

- **fab deploy:** Pushes content, deploys static files and restarts the Gunicorn process via PM2.
- **fab migrate:** Additionally updates packages and applies database migrations.

Enjoy building your project with this template—it’s designed to accelerate development while
keeping configurations clean and manageable.

## Installation

Ensure you have the required tools installed:

```bash
pip install django      # for django-admin startproject
brew install uv direnv  # macOS; see https://docs.astral.sh/uv/getting-started/installation/ for other platforms
```

Python 3.14 is the project default.

To create a new project from this template:

```bash
django-admin startproject \
--template=https://github.com/kakulukia/django-default-project/zipball/master \
<new_project_name>
```

Then, navigate into your project:

```bash
cd <new_project_name>
direnv allow        # creates .venv and runs uv sync automatically
git init
pre-commit install
```

After initial setup, customize your settings by copying one of the default environment files:

```bash
cp settings/andy.py settings/your_name.py
```

And set your environment variable to use your custom settings by default:

```bash
export DJANGO_SETTINGS_MODULE=settings.your_name
```

## Dependency Updates

Check which dependencies would be updated:

```bash
uv lock --upgrade --dry-run
```

Run the actual dependency update:

```bash
uv lock --upgrade
```

## 1st Time Deployment

**Required Components:**

- A recent Ubuntu (or similar) server distribution.
- **Nginx:**
    ```bash
    sudo apt install nginx
    ```
- **Node.js (latest LTS):**
    ```bash
    curl -fsSL https://fnm.vercel.app/install | bash

    fnm install --lts  # or the latest LTS version - used for pm2 and sass
    ```
- **pm2 (process manager):**
    ```bash
    npm install -g pm2 sass
    ```
- Set up your project directory (e.g., under `/opt/www/<project_name>`):
    ```bash
    sudo mkdir -p /opt/www/<project_name>
    sudo chown -R $USER:$USER /opt/www/<project_name>
    cd /opt/www/<project_name>
    ```
- **uv** (Python version management + dependency installation):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
- **Direnv Setup:**
    ```bash
    sudo apt install direnv
    ```
- Adjust the supplied Nginx configuration to your needs, link it to `sites-enabled`, and
reload Nginx:
    ```bash
    sudo ln -s /opt/www/<project>/settings/deployment/project.nginx /etc/nginx/sites-enabled/<project>
    sudo nginx -t
    sudo nginx -s reload
    ```
- Run `direnv allow` to create the venv and install dependencies, then initialize secrets:
    ```bash
    direnv allow
    python manage.py runserver
    ```
- Test the Gunicorn configuration:
    ```bash
    .venv/bin/gunicorn --check-config \
      --chdir /opt/www/<project> \
      --env DJANGO_SETTINGS_MODULE=settings \
      settings.wsgi:application
    ```
- If everything works, start the pm2 job and set it to launch on startup:
    ```bash
    cd settings/deployment
    PROJECT_NAME=<project> DJANGO_SETTINGS_MODULE=settings pm2 start project.sh --name <project>
    pm2 save
    pm2 startup
    cd -
    ```
- Prepare Django static files:
    ```bash
    python manage.py compress -e pug,html --force
    python manage.py collectstatic --noinput
    ```

Your project should now be up and running. For deploying updates, you can use the provided fabfile.

- Optionally, deploy an SSL certificate via Certbot:
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx
    ```
