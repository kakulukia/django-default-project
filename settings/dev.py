from .common import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]
CSRF_TRUSTED_ORIGINS = []

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INSTALLED_APPS += [  # noqa
    # debugging
    "debug_toolbar",
    "django_browser_reload",
]
MIGRATION_MODULES = {"debug_toolbar": None}  # this disables migrations for debug toolbar

DEBUG_TOOLBAR_PANELS = (
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    # "djdt_flamegraph.FlamegraphPanel",  # needs --nothreading --noreload
)

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": (
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "djdt_flamegraph.FlamegraphPanel",
    )
}

MIDDLEWARE += [  # noqa
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

INTERNAL_IPS = ALLOWED_HOSTS

# unset sentry configuration for development
# sentry_sdk.init()  # noqa

POST_OFFICE = {"BACKENDS": {"default": "django.core.mail.backends.console.EmailBackend"}}
COMPRESS_OFFLINE = False
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa
DJANGO_RUNSERVER_HIDE_WARNING = True
