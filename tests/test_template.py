import os
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from cookiecutter.exceptions import FailedHookException
from cookiecutter.main import cookiecutter

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "{{ cookiecutter.project_slug }}"


class TemplateTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def generate(self, **context):
        return Path(
            cookiecutter(
                str(ROOT),
                no_input=True,
                extra_context=context,
                output_dir=str(self.output),
                default_config={
                    "cookiecutters_dir": str(self.output / "cache"),
                    "replay_dir": str(self.output / "replay"),
                },
            )
        )

    def test_generated_project(self):
        project = self.generate(author_name="Alex Example")
        metadata = tomllib.loads((project / "pyproject.toml").read_text())["project"]
        self.assertEqual(project.name, "my-project")
        self.assertEqual(metadata["name"], project.name)
        self.assertEqual(metadata["version"], "0.1.0")
        self.assertNotIn("urls", metadata)
        lock = tomllib.loads((project / "uv.lock").read_text())
        package = next(p for p in lock["package"] if p["source"] == {"virtual": "."})
        self.assertEqual(package["name"], metadata["name"])
        self.assertEqual(package["version"], metadata["version"])

        for directory in (
            "assets",
            "templates",
            "scripts",
            ".claude",
            ".codex",
            ".codegraph",
        ):
            for source in (TEMPLATE / directory).rglob("*"):
                if source.is_file():
                    relative = source.relative_to(TEMPLATE)
                    self.assertEqual(
                        source.read_bytes(),
                        (project / relative).read_bytes(),
                        str(relative),
                    )
        for name in (".gitignore", ".editorconfig", ".pre-commit-config.yaml"):
            self.assertEqual((TEMPLATE / name).read_bytes(), (project / name).read_bytes())
        self.assertFalse((TEMPLATE / ".envrc").exists())
        self.assertEqual((TEMPLATE / "{{ '.envrc' }}").read_bytes(), (project / ".envrc").read_bytes())
        for name in (
            "scripts/uv-update",
            "settings/deployment/project.sh",
            "settings/deployment/worker.sh",
        ):
            self.assertTrue(os.access(project / name, os.X_OK), name)
            subprocess.run(["bash", "-n", str(project / name)], check=True)
        for name in (
            ".git",
            ".beads",
            "graphify-out",
            ".venv",
            "db.sqlite3",
            "my_secrets/secrets.py",
            "cookiecutter.json",
            "hooks",
            "tests",
            "misc",
        ):
            self.assertFalse((project / name).exists(), name)
        self.assertIn('APP_NAME = "my-project"', (project / "fabfile.py").read_text())
        self.assertIn(
            "${PROJECT_NAME:-my-project}",
            (project / "settings/deployment/project.sh").read_text(),
        )
        self.assertIn(
            "/tmp/my-project.gunicorn.sock",
            (project / "settings/deployment/project.nginx").read_text(),
        )
        self.assertNotIn("django-default-project", (project / "README.md").read_text())
        self.assertEqual((project / "settings/alex.py").read_text(), "from .dev import *  # noqa\n")

        env = os.environ | {
            "DJANGO_SETTINGS_MODULE": "settings.alex",
            "SECRET_KEY": "test-only-cookiecutter-secret-key",
            "SENTRY_DSN": "",
        }
        env.pop("UV_PROJECT_ENVIRONMENT", None)
        env.pop("VIRTUAL_ENV", None)
        env.pop("PYTHONPATH", None)
        lock_before = (project / "uv.lock").read_bytes()
        subprocess.run(["uv", "sync", "--locked"], cwd=project, env=env, check=True)
        check = ["uv", "run", "--locked", "python", "manage.py", "check"]
        subprocess.run(check, cwd=project, env=env, input="\n", text=True, check=True)
        subprocess.run(check, cwd=project, env=env, input="", text=True, check=True)
        help_result = subprocess.run(
            ["uv", "run", "--locked", "python", "manage.py", "runserver", "--nostatic", "--help"],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("--nostatic", help_result.stdout)
        for command in (
            [
                "uv",
                "run",
                "--locked",
                "python",
                "manage.py",
                "test",
                "users",
                "utils",
                "--noinput",
            ],
            ["uv", "run", "--locked", "ruff", "check", "."],
            ["uv", "run", "--locked", "ruff", "format", "--check", "."],
        ):
            subprocess.run(command, cwd=project, env=env, check=True)
        self.assertEqual(lock_before, (project / "uv.lock").read_bytes())

    def test_custom_metadata(self):
        context = {
            "project_name": "Über Portal",
            "project_slug": "customer-portal",
            "description": 'Quotes "and" backslashes \\ and a newline\nwith Unicode: Grüße.',
            "author_name": 'Zoë "Example"',
            "author_email": "zoe@example.org",
            "repository_url": "https://example.org/team/customer-portal",
        }
        project = self.generate(**context)
        metadata = tomllib.loads((project / "pyproject.toml").read_text())["project"]
        self.assertEqual(metadata["name"], context["project_slug"])
        self.assertEqual(metadata["description"], context["description"])
        self.assertEqual(
            metadata["authors"],
            [{"name": context["author_name"], "email": context["author_email"]}],
        )
        self.assertEqual(metadata["urls"], {"repository": context["repository_url"]})
        self.assertTrue((project / "README.md").read_text().startswith("# Über Portal\n"))
        self.assertEqual((project / "settings/zoe.py").read_text(), "from .dev import *  # noqa\n")

    def test_author_settings_names(self):
        for author, module in (
            ("Jean-Luc Picard", "jean_luc"),
            ("Your Name", "your"),
            ("   ", "developer"),
            ("Dev Patel", "dev_local"),
            ("Common Name", "common_local"),
            ("Urls Name", "urls_local"),
            ("Wsgi Name", "wsgi_local"),
            ("Asgi Name", "asgi_local"),
        ):
            with self.subTest(author=author):
                project = self.generate(project_slug=module.replace("_", "-"), author_name=author)
                self.assertEqual((project / f"settings/{module}.py").read_text(), "from .dev import *  # noqa\n")
                for name in ("common", "dev", "urls", "wsgi", "asgi"):
                    self.assertEqual(
                        (project / f"settings/{name}.py").read_bytes(), (TEMPLATE / f"settings/{name}.py").read_bytes()
                    )
        for author in ("123 Name", "!!!", "class Name"):
            with self.subTest(author=author):
                with self.assertRaises(FailedHookException):
                    self.generate(author_name=author)
                self.assertFalse((self.output / "my-project").exists())

    def test_invalid_slug(self):
        for slug in ("Uppercase", "with spaces", "bad_name", "bad--name", 'bad"name'):
            with self.subTest(slug=slug):
                with self.assertRaises(FailedHookException):
                    self.generate(project_slug=slug)
                self.assertFalse((self.output / slug).exists())


if __name__ == "__main__":
    unittest.main()
