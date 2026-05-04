from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.sites.models import Site
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from users.models import User


class UserViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.data.create_user(username="user", email="user@example.com", password="password")
        self.other_user = User.data.create_user(username="other", email="other@example.com", password="password")
        self.staff_user = User.data.create_user(
            username="staff",
            email="staff@example.com",
            password="password",
            is_staff=True,
        )

    def test_non_staff_user_only_sees_self_in_user_list(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.user.id)

    def test_non_staff_user_cannot_fetch_other_user_detail(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(f"/api/users/{self.other_user.id}/")

        self.assertEqual(response.status_code, 404)

    def test_staff_user_sees_all_users(self):
        self.client.force_authenticate(self.staff_user)

        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual({user["id"] for user in response.data}, {self.user.id, self.other_user.id, self.staff_user.id})

    def test_me_returns_authenticated_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.user.id)


class UserEmailUserTest(TestCase):
    def setUp(self):
        self.user = User.data.create_user(username="user", email="user@example.com", password="password")
        site = Site.objects.get_current()
        site.domain = "example.com"
        site.save(update_fields=["domain"])
        Site.objects.clear_cache()

    @override_settings(SECURE_SSL_REDIRECT=True, EMAIL_OVERRIDE_ADDRESS=None, DEFAULT_FROM_EMAIL="from@example.com")
    @patch("users.models.mail.send")
    def test_email_user_uses_https_site_base_url_when_ssl_redirect_is_enabled(self, mock_send):
        self.user.email_user(
            "template-name",
            context={"existing": "value"},
            request=SimpleNamespace(is_secure=lambda: True),
        )

        mock_send.assert_called_once()
        kwargs = mock_send.call_args.kwargs
        self.assertEqual(kwargs["context"]["base_url"], "https://example.com")
        self.assertEqual(kwargs["context"]["existing"], "value")

    @override_settings(SECURE_SSL_REDIRECT=False, EMAIL_OVERRIDE_ADDRESS=None, DEFAULT_FROM_EMAIL="from@example.com")
    @patch("users.models.mail.send")
    def test_email_user_uses_http_site_base_url_when_ssl_redirect_is_disabled(self, mock_send):
        self.user.email_user("template-name", request=SimpleNamespace(is_secure=lambda: False))

        mock_send.assert_called_once()
        kwargs = mock_send.call_args.kwargs
        self.assertEqual(kwargs["context"]["base_url"], "http://example.com")
