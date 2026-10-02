#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-settings}"

cd "${PROJECT_DIR}"
exec "${PROJECT_DIR}/.venv/bin/python" -u manage.py db_worker --no-reload
