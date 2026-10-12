import re
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.tasks import TaskResultStatus
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from utils.tasks import calculate_meaning_of_life


class DeploymentCommandsTest(SimpleTestCase):
    def test_deployments_install_cron_in_project_and_restart_both_processes(self):
        import fabfile

        for deploy in (fabfile.deploy, fabfile.migrate):
            with self.subTest(deploy=deploy.__name__):
                calls = []
                with patch("fabfile.run", side_effect=lambda command: calls.append((command, fabfile.env.cwd))):
                    deploy()

                commands = [command for command, _ in calls]
                cron = "uv run ./manage.py installtasks"
                self.assertEqual(commands.count(cron), 1)
                for command, cwd in calls:
                    if command.startswith("uv run ./manage.py "):
                        self.assertEqual(cwd, fabfile.env.path, command)
                for name in (fabfile.APP_NAME, f"{fabfile.APP_NAME}-worker"):
                    restart = f"pm2 restart {name}"
                    self.assertIn(restart, commands)
                    self.assertLess(commands.index(cron), commands.index(restart))


class BackgroundTaskTest(TransactionTestCase):
    def test_database_worker_executes_native_task(self):
        result = calculate_meaning_of_life.enqueue()
        self.assertEqual(result.status, TaskResultStatus.READY)

        call_command("db_worker", batch=True, reload=False, startup_delay=False, verbosity=0)

        result.refresh()
        self.assertEqual(result.status, TaskResultStatus.SUCCESSFUL)
        self.assertEqual(result.return_value, 42)


class ProjectSettingsTest(SimpleTestCase):
    def test_time_zone_observes_berlin_daylight_saving_time(self):
        self.assertEqual(settings.TIME_ZONE, "Europe/Berlin")

    def test_wsgi_application_loads(self):
        from settings.wsgi import application

        self.assertIsNotNone(application)

    def test_asgi_application_loads(self):
        from settings.asgi import application

        self.assertIsNotNone(application)


class CoreUrlsTest(TestCase):
    def test_both_signup_urls_start_with_email_only(self):
        for url in ("/accounts/signup/", "/accounts/signup/passkey/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(set(response.context["form"].fields), {"email"})
                self.assertContains(response, 'action="/accounts/signup/"')
                self.assertNotContains(response, 'name="password1"')

    def test_account_dialog_allows_only_same_origin_frames(self):
        for url in (
            "/",
            "/accounts/login/",
            "/accounts/signup/",
            "/accounts/signup/passkey/",
            "/accounts/2fa/webauthn/signup/",
            "/accounts/password/reset/",
            "/accounts/2fa/",
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        for url in ("/admin/login/", "/api/users/", "/accounts/nonexistent/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        response = self.client.post("/accounts/signup/passkey/", {"email": "invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")

    def test_index_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_frontend_assets_and_css_dependencies_are_local_and_complete(self):
        for template in ("index.pug", "500.pug"):
            with self.subTest(template=template):
                assets = re.findall(
                    r"<(?:script|link)\b[^>]*\b(?:src|href)=[\"\']([^\"\']+)",
                    render_to_string(template),
                )
                self.assertTrue(assets, template)
                checked = set()
                while assets:
                    asset = assets.pop()
                    if asset in checked:
                        continue
                    checked.add(asset)
                    parsed = urlsplit(asset)
                    self.assertFalse(parsed.scheme or parsed.netloc, asset)
                    self.assertTrue(parsed.path.startswith(settings.STATIC_URL), asset)
                    path = finders.find(unquote(parsed.path.removeprefix(settings.STATIC_URL)))
                    self.assertIsNotNone(path, asset)
                    if parsed.path.endswith(".css"):
                        for dependency in re.findall(r"url\(\s*([^)]*?)\s*\)", Path(path).read_text()):
                            dependency = dependency.strip("\"'")
                            if not dependency.startswith("data:"):
                                assets.append(urljoin(asset, dependency))

    def test_admin_redirects_anonymous_to_login(self):
        response = self.client.get("/admin/")
        self.assertRedirects(response, "/admin/login/?next=/admin/", fetch_redirect_response=False)

    def test_api_requires_authentication(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 403)
