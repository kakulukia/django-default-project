from django.conf import settings
from django.test import SimpleTestCase, TestCase


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
