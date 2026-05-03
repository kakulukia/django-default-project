from django.test import TestCase
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
