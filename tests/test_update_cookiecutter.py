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
                'if [[ -n "${UPDATE_TEST_REMOTE_MAIN:-}" ]]; then\n'
                '  git update-ref refs/remotes/origin/main "$UPDATE_TEST_REMOTE_MAIN"\n'
                "fi\n"
                'exit "${UPDATE_TEST_EXIT:-0}"\n',
            ),
            ("sass", "#!/usr/bin/env bash\nexit 0\n"),
        ):
            path = binaries / name
            path.write_text(content)
            path.chmod(0o755)
        shutil.copy2(ROOT / "update-cookiecutter", self.repo / "update-cookiecutter")
        shutil.copy2(ROOT / ".gitignore", self.repo / ".gitignore")
        self.git("init", "-b", "dev")
        self.git("config", "user.name", "Workflow test")
        self.git("config", "user.email", "workflow@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", str(self.output / "no-hooks"))
        self.project = self.repo / "project"
        self.project.mkdir()
        (self.project / "module.py").write_text("value = 'original'\n")
        self.commit("Runnable project")
        self.git("switch", "-c", "main")
        self.template = self.repo / "{{ cookiecutter.project_slug }}"
        self.project.rename(self.template)
        self.commit("Cookiecutter layout")
        self.git("switch", "dev")

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
        development = self.git("rev-parse", "dev")

        result = self.update()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "dev")
        self.assertEqual(self.git("rev-parse", "dev"), development)
        self.git("merge-base", "--is-ancestor", "dev", "main")
        self.assertEqual(self.git("show", "main:{{ cookiecutter.project_slug }}/module.py"), "value = 'updated'")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.log.read_text(), "validation\n")

    def test_update_can_start_from_main(self):
        (self.project / "module.py").write_text("value = 'updated'\n")
        self.commit("Application update")
        development = self.git("rev-parse", "dev")
        self.git("switch", "main")

        result = self.update()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("branch", "--show-current"), "main")
        self.assertEqual(self.git("rev-parse", "dev"), development)
        self.assertEqual((self.template / "module.py").read_text(), "value = 'updated'\n")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_publish_command_keeps_original_lease_and_does_not_push(self):
        remote = self.output / "remote.git"
        self.git("init", "--bare", str(remote))
        self.git("remote", "add", "origin", str(remote))
        self.git("push", "origin", "main")
        expected_main = self.git("rev-parse", "origin/main")
        (self.project / "module.py").write_text("value = 'updated'\n")
        self.commit("Application update")
        self.env["UPDATE_TEST_REMOTE_MAIN"] = self.git("rev-parse", "dev")

        result = self.update()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"git push --force-with-lease=refs/heads/main:{expected_main} origin main", result.stdout)
        self.assertNotEqual(self.git("rev-parse", "origin/main"), expected_main)
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/main").split()[0], expected_main)

    def test_new_application_files_follow_directory_rename(self):
        self.git("config", "merge.renames", "false")
        self.git("config", "merge.directoryRenames", "false")
        (self.project / "new_module.py").write_text("value = 'new'\n")
        self.commit("New application file")

        result = self.update()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("show", "main:{{ cookiecutter.project_slug }}/new_module.py"), "value = 'new'")
        files = self.git("ls-tree", "-r", "--name-only", "main").splitlines()
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
                self.assertEqual(self.git("branch", "--show-current"), "dev")
                self.assertEqual((self.project / "module.py").read_text(), "value = 'local work'\n")
                self.assertFalse(self.log.exists())

    def test_untracked_files_are_preserved(self):
        (self.repo / "local.txt").write_text("local work\n")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "dev")
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
        self.git("branch", "-m", "main", "feature/other")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "dev")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertFalse(self.log.exists())

    def test_missing_development_branch_keeps_original_checkout(self):
        self.git("branch", "-m", "dev", "feature/other")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "feature/other")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertFalse(self.log.exists())

    def test_conflict_stops_before_validation_and_preserves_development(self):
        self.git("switch", "main")
        (self.template / "module.py").write_text("value = 'template'\n")
        self.commit("Template edit")
        self.git("switch", "dev")
        (self.project / "module.py").write_text("value = 'application'\n")
        self.commit("Application edit")
        development = self.git("rev-parse", "dev")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("rev-parse", "dev"), development)
        self.assertTrue((self.repo / ".git/rebase-merge").is_dir())
        self.assertIn("<<<<<<<", (self.template / "module.py").read_text())
        self.assertFalse(self.log.exists())

    def test_validation_failure_keeps_template_available_for_inspection(self):
        self.env["UPDATE_TEST_EXIT"] = "1"
        development = self.git("rev-parse", "dev")

        result = self.update()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "main")
        self.assertEqual(self.git("rev-parse", "dev"), development)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.log.read_text(), "validation\n")


if __name__ == "__main__":
    unittest.main()
