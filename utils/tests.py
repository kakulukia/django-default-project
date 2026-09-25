from django.conf import settings
from django.core.management import call_command
from django.tasks import TaskResultStatus
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from utils.tasks import calculate_meaning_of_life


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
    def test_index_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_admin_redirects_anonymous_to_login(self):
        response = self.client.get("/admin/")
        self.assertRedirects(response, "/admin/login/?next=/admin/", fetch_redirect_response=False)

    def test_api_requires_authentication(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 403)
