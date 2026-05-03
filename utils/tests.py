from django.conf import settings
from django.test import SimpleTestCase


class ProjectSettingsTest(SimpleTestCase):
    def test_time_zone_observes_berlin_daylight_saving_time(self):
        self.assertEqual(settings.TIME_ZONE, "Europe/Berlin")
