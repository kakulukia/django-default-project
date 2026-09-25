import re
import sys

project_slug = {{ cookiecutter.project_slug | tojson }}

if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", project_slug):
    sys.exit("project_slug must start with a lowercase letter and contain only lowercase letters, digits and single hyphens.")
