#!/usr/bin/env bash
set -euo pipefail

# determine directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# invoke the WSGI handler from the venv in the project root
"${SCRIPT_DIR}/../.venv/bin/gunicorn" --env DJANGO_SETTINGS_MODULE=settings --workers 4 --bind unix:/tmp/project.socket settings.wsgi

# use this version for testing
#gunicorn settings.wsgi
