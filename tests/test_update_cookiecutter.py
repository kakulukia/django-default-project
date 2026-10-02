import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UpdateCookiecutterTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)
        self.repo = self.output / "repo"
        self.repo.mkdir()
        binaries = self.output / "bin"
        binaries.mkdir()
        self.log = self.output / "validation.log"
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(
            PATH=f"{binaries}{os.pathsep}{self.env['PATH']}",
            UPDATE_TEST_LOG=str(self.log),
            VIRTUAL_ENV="test-existing-environment",
            UV_PROJECT_ENVIRONMENT="test-existing-project-environment",
            PYTHONPATH="test-existing-python-path",
        )
        for name, content in (
            (
                "uv",
                "#!/usr/bin/env bash\n"
                '[[ -z "${VIRTUAL_ENV+x}${UV_PROJECT_ENVIRONMENT+x}${PYTHONPATH+x}" ]] || exit 97\n'
                'printf "validation\\n" >> "$UPDATE_TEST_LOG"\n'
                'exit "${UPDATE_TEST_EXIT:-0}"\n',
            ),
            ("sass", "#!/usr/bin/env bash\nexit 0\n"),
        ):
            path = binaries / name
            path.write_text(content)
            path.chmod(0o755)
        shutil.copy2(ROOT / "update-cookiecutter", self.repo / "update-cookiecutter")
        shutil.copy2(ROOT / ".gitignore", self.repo / ".gitignore")
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Workflow test")
        self.git("config", "user.email", "workflow@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", str(self.output / "no-hooks"))
        self.project = self.repo / "project"
        self.project.mkdir()
        (self.project / "module.py").write_text("value = 'original'\n")
        self.commit("Runnable project")
        self.git("switch", "-c", "feature/cookiecutter")
        self.template = self.repo / "{{ cookiecutter.project_slug }}"
        self.project.rename(self.template)
        self.commit("Cookiecutter layout")
        self.git("switch", "main")

    def git(self, *arguments):
        return subprocess.run(
            ["git", *arguments], cwd=self.repo, env=self.env, capture_output=True, text=True, check=True
        ).stdout.strip()

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "-m", message)

    def update(self):
        return subprocess.run(
            [str(self.repo / "update-cookiecutter")], cwd=self.output, env=self.env, capture_output=True, text=True
        )

    def test_rebase_carries_application_changes_and_returns_to_original_branch(self):
        (self.project / "module.py").write_text("value = 'updated'\n")
        self.commit("Application update")
        main = self.git("rev-parse", "main")

        result = self.update()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "main")
        self.assertEqual(self.git("rev-parse", "main"), main)
        self.git("merge-base", "--is-ancestor", "main", "feature/cookiecutter")
        self.assertEqual(
            self.git("show", "feature/cookiecutter:{{ cookiecutter.project_slug }}/module.py"), "value = 'updated'"
        )
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.log.read_text(), "validation\n")

    def test_new_application_files_follow_directory_rename(self):
        self.git("config", "merge.renames", "false")
        self.git("config", "merge.directoryRenames", "false")
        (self.project / "new_module.py").write_text("value = 'new'\n")
        self.commit("New application file")

        result = self.update()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            self.git("show", "feature/cookiecutter:{{ cookiecutter.project_slug }}/new_module.py"), "value = 'new'"
        )
        files = self.git("ls-tree", "-r", "--name-only", "feature/cookiecutter").splitlines()
        self.assertFalse(any(name.startswith("project/") for name in files))
        self.assertEqual(self.git("config", "merge.renames"), "false")
        self.assertEqual(self.git("config", "merge.directoryRenames"), "false")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_dirty_and_staged_changes_are_preserved(self):
        (self.project / "module.py").write_text("value = 'local work'\n")
        for staged in (False, True):
            with self.subTest(staged=staged):
                if staged:
                    self.git("add", "project/module.py")
                before = self.git("status", "--porcelain")

                result = self.update()

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.git("status", "--porcelain"), before)
                self.assertEqual(self.git("branch", "--show-current"), "main")
                self.assertEqual((self.project / "module.py").read_text(), "value = 'local work'\n")
                self.assertFalse(self.log.exists())

    def test_untracked_files_are_preserved(self):
        (self.repo / "local.txt").write_text("local work\n")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "main")
        self.assertEqual((self.repo / "local.txt").read_text(), "local work\n")
        self.assertFalse(self.log.exists())

    def test_secret_files_remain_ignored_across_application_layouts(self):
        secrets = [directory / "my_secrets/secrets.py" for directory in (self.project, self.template)]
        for secret in secrets:
            secret.parent.mkdir(parents=True)
            secret.write_text("local_test_value = 'test-only'\n")
        self.git("add", "--all")
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")

        result = self.update()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.git("add", "--all")
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")
        for secret in secrets:
            self.assertEqual(secret.read_text(), "local_test_value = 'test-only'\n")

    def test_missing_template_branch_keeps_original_checkout(self):
        self.git("branch", "-m", "feature/cookiecutter", "feature/other")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "main")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertFalse(self.log.exists())

    def test_conflict_stops_before_validation_and_preserves_main(self):
        self.git("switch", "feature/cookiecutter")
        (self.template / "module.py").write_text("value = 'template'\n")
        self.commit("Template edit")
        self.git("switch", "main")
        (self.project / "module.py").write_text("value = 'application'\n")
        self.commit("Application edit")
        main = self.git("rev-parse", "main")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("rev-parse", "main"), main)
        self.assertTrue((self.repo / ".git/rebase-merge").is_dir())
        self.assertIn("<<<<<<<", (self.template / "module.py").read_text())
        self.assertFalse(self.log.exists())

    def test_validation_failure_keeps_template_available_for_inspection(self):
        self.env["UPDATE_TEST_EXIT"] = "1"
        main = self.git("rev-parse", "main")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "feature/cookiecutter")
        self.assertEqual(self.git("rev-parse", "main"), main)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.log.read_text(), "validation\n")


if __name__ == "__main__":
    unittest.main()
