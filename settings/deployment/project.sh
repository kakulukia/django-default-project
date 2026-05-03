#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PROJECT_NAME="${PROJECT_NAME:-project}"
DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-settings}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_SOCKET="${GUNICORN_SOCKET:-/tmp/${PROJECT_NAME}.gunicorn.sock}"

exec "${PROJECT_DIR}/.venv/bin/gunicorn" \
  --chdir "${PROJECT_DIR}" \
  --env "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}" \
  --workers "${GUNICORN_WORKERS}" \
  --bind "unix:${GUNICORN_SOCKET}" \
  --access-logfile - \
  --error-logfile - \
  settings.wsgi:application
