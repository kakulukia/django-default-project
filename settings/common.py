"""Default production settings.

The ``settings`` package imports this module by default. Development settings
import it and explicitly relax local-only behavior in ``settings/dev.py``.
"""

from pathlib import Path

import sentry_sdk
from django.urls import reverse_lazy
from icecream import install
from pypugjs.ext.django.compiler import enable_pug_translations

from my_secrets import secrets

enable_pug_translations()
install()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Use the path of this settings file to correctly detect the right path to the project root.
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = secrets.SECRET_KEY
SITE_ID = 1

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = [
    "example.com",
    # "www.example.com",
]
CSRF_TRUSTED_ORIGINS = [
    "https://example.com",
    # "https://www.example.com",
]

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 3600
# Keep these off in the template. Enable them in a project-specific production
# settings module only after every affected subdomain is HTTPS-only and
# preload-ready.
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
INSTALLED_APPS = [
    # our own stuff
    "sample_app",
    "users",
    "utils",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    # 3rd party apps
    "axes",
    "compressor",
    "django_extensions",
    "django_secrets",
    "django_tasks",
    "django_tasks_db",
    "loginas",
    "kronos",
    "post_office",
    "rest_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "axes.backends.AxesBackend",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                # PyPugJS part:   ##############################
                (
                    "pypugjs.ext.django.Loader",
                    (
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ),
                )
            ],
            "builtins": ["pypugjs.ext.django.templatetags"],
        },
    }
]

AUTH_USER_MODEL = "users.User"
ROOT_URLCONF = "settings.urls"
WSGI_APPLICATION = "settings.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "transaction_mode": "IMMEDIATE",
            "timeout": 5,  # seconds
            "init_command": """
                    PRAGMA journal_mode=WAL;
                    PRAGMA synchronous=NORMAL;
                    PRAGMA mmap_size = 134217728;
                    PRAGMA auto_vacuum = FULL;
                    PRAGMA journal_size_limit = 27103364;
                    PRAGMA cache_size=2000;
                    PRAGMA auto_vacuum=INCREMENTAL;
                """,
        },
    }
    # PLEASE, as soon as the project gets a lil more serious => use Postgres!
    # BUT the new WAL mode of SQLite should be good enough for small to medium projects
    #############################################################################################
    #  'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'db_name',
    #     'USER': 'username',
    #     'PASSWORD': secrets.DB_PASSWORD,
    #     'HOST': '127.0.0.1',
    #     'PORT': '5432',
    #     'ATOMIC_REQUESTS': True,  # enables automatic rollback on broken requests
    # }
}
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "axes_cache": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
}
TASKS = {"default": {"BACKEND": "django_tasks_db.DatabaseBackend"}}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AXES_FAILURE_LIMIT = 2
AXES_CACHE = "axes_cache"
AXES_LOCKOUT_PARAMETERS = ["ip_address", ["username", "user_agent"]]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/
LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True


STATICFILES_DIRS = [BASE_DIR / "assets"]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
COMPRESS_PRECOMPILERS = (("text/x-sass", "sass {infile} {outfile}"),)
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True


_sentry_dsn = getattr(secrets, "SENTRY_DSN", None)
if _sentry_dsn and _sentry_dsn.startswith("https://"):
    sentry_sdk.init(
        dsn=_sentry_dsn,
        send_default_pii=True,
        traces_sample_rate=0.2,
    )

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

EMAIL_OVERRIDE_ADDRESS = None
EMAIL_FOOTER = ""
DEFAULT_FROM_EMAIL = "webmaster@example.com"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_BACKEND = "post_office.EmailBackend"

SILENCED_SYSTEM_CHECKS = ["debug_toolbar.W006"]


def can_login_as(request, target_user):
    return request.user.is_superuser and not target_user.is_superuser


CAN_LOGIN_AS = can_login_as
LOGINAS_REDIRECT_URL = "/admin/"
LOGINAS_LOGOUT_REDIRECT_URL = reverse_lazy("admin:index")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "utils.IsOwnerOrSuperAdmin",
    ],
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "utils.NoFormBrowsableAPIRenderer",  # removes the form and thus a lot of unnecessary queries
    ),
}
