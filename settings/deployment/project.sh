#!/usr/bin/env bash
#gunicorn --env DJANGO_SETTINGS_MODULE=settings --workers 4 --bind unix:/tmp/project.socket settings.wsgi
# use the version for testing
gunicorn settings.wsgi
