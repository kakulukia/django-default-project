#!/usr/bin/env bash

# production version
gunicorn --env DJANGO_SETTINGS_MODULE=settings --workers 4 --bind unix:/tmp/project.socket settings.wsgi

# use this version for testing
#gunicorn settings.wsgi
