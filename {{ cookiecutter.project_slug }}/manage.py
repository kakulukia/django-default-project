#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    from django_secrets import startup

    # django-secrets treats empty values as missing; persist a disabled marker for Sentry.
    prompt_for_secret = startup.prompt_for_secret
    startup.prompt_for_secret = lambda key: prompt_for_secret(key) or ("none" if key == "SENTRY_DSN" else "")
    try:
        startup.check()
    finally:
        startup.prompt_for_secret = prompt_for_secret

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
