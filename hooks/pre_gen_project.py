import keyword
import re
import sys

project_slug = {{ cookiecutter.project_slug | tojson }}

if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", project_slug):
    sys.exit("project_slug must start with a lowercase letter and contain only lowercase letters, digits and single hyphens.")

author_settings = {{ cookiecutter.__author_settings | tojson }}
if not author_settings.isidentifier() or keyword.iskeyword(author_settings):
    sys.exit("The author's first name must produce a valid Python module name after normalization.")
if author_settings in {"common", "dev", "urls", "wsgi", "asgi", "__init__"}:
    sys.exit("The generated personal settings module must not overwrite a shared settings module.")
