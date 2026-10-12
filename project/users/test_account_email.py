import re
from contextlib import redirect_stdout
from email import message_from_string
from io import StringIO
from urllib.parse import urlsplit

from allauth.account.models import EmailAddress
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from post_office.models import STATUS, Email, EmailTemplate

from settings import dev
from users.models import User


@override_settings(EMAIL_BACKEND="post_office.EmailBackend", POST_OFFICE={"DEFAULT_PRIORITY": "medium"})
class AccountEmailTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client.defaults["HTTP_HOST"] = "localhost:8001"

    def test_invitation_is_queued_and_link_prefills_signup_without_creating_a_user(self):
        output = StringIO()
        call_command("invite_user", "new+demo@example.com", base_url="http://localhost:8001", stdout=output)

        email = Email.objects.get()
        self.assertEqual(email.status, STATUS.queued)
        self.assertEqual(email.to, ["new+demo@example.com"])
        self.assertEqual(email.template.name, "account_invitation")
        self.assertIn("http://localhost:8001/?account=signup&email=new%2Bdemo%40example.com", email.message)
        self.assertIn(email.message, output.getvalue())
        self.assertFalse(User.data.exists())
        response = self.client.get(reverse("demo"), {"account": "signup", "email": "new+demo@example.com"})
        self.assertContains(response, "account-dialog")
        self.assertNotContains(response, "iframe")
        self.assertNotIn("_auth_user_id", self.client.session)

        preview = StringIO()
        call_command("show_email", email.pk, stdout=preview)
        self.assertIn(email.message, preview.getvalue())
        email.refresh_from_db()
        self.assertEqual(email.status, STATUS.queued)

    def test_invitation_preserves_custom_template_and_rejects_invalid_input(self):
        template = EmailTemplate.objects.create(name="account_invitation", subject="Custom", content="{{ signup_url }}")
        call_command("invite_user", "new@example.com", base_url="http://localhost:8001", stdout=StringIO())
        template.refresh_from_db()
        self.assertEqual(template.subject, "Custom")
        for options in (
            {"email": "invalid", "base_url": "http://localhost:8001"},
            {"email": "new@example.com", "base_url": "javascript:alert(1)"},
            {"email": "new@example.com", "base_url": "https://user:password@example.com"},
            {"email": "new@example.com", "base_url": "http://["},
            {"email": "new@example.com", "base_url": "http://localhost:invalid"},
        ):
            with self.subTest(options=options), self.assertRaises(CommandError):
                call_command("invite_user", options["email"], base_url=options["base_url"], stdout=StringIO())
        self.assertEqual(Email.objects.count(), 1)

    def test_verification_email_is_visible_in_post_office(self):
        self.client.post(reverse("account_signup_by_passkey"), {"email": "new@example.com"})

        email = Email.objects.get()
        self.assertEqual(email.to, ["new@example.com"])
        self.assertEqual(email.status, STATUS.queued)
        self.assertIn(self.client.session["account_email_verification_code"]["code"], email.message)

    def test_password_reset_uses_queued_one_time_link_for_password_and_passkey_accounts(self):
        for password in ("previous-password", None):
            with self.subTest(password_account=password is not None):
                cache.clear()
                user = User.data.create_user(
                    username=f"reset-{User.data.count()}",
                    email=f"reset-{User.data.count()}@example.com",
                    password=password,
                )
                EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
                response = self.client.post(reverse("account_reset_password"), {"email": user.email})
                self.assertRedirects(response, reverse("account_reset_password_done"))
                email = Email.objects.filter(to__contains=user.email).latest("pk")
                reset_url = re.search(r"http://localhost:8001/\S+/key/\S+", email.message).group()
                response = self.client.get(urlsplit(reset_url).path, follow=True)
                self.assertEqual(response.status_code, 200)
                form_url = response.request["PATH_INFO"]
                response = self.client.post(form_url, {"password1": "short", "password2": "short"})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                user.refresh_from_db()
                self.assertEqual(user.has_usable_password(), password is not None)
                response = self.client.post(
                    form_url, {"password1": "Strong-new-password-492!", "password2": "Strong-new-password-492!"}
                )
                self.assertRedirects(response, reverse("account_reset_password_from_key_done"))
                user.refresh_from_db()
                self.assertTrue(user.check_password("Strong-new-password-492!"))
                self.assertNotIn("_auth_user_id", self.client.session)
                self.client.get(urlsplit(reset_url).path)
                self.client.post(
                    form_url, {"password1": "Different-password-349!", "password2": "Different-password-349!"}
                )
                user.refresh_from_db()
                self.assertTrue(user.check_password("Strong-new-password-492!"))

    def test_unknown_account_reset_does_not_reveal_account_existence(self):
        response = self.client.post(reverse("account_reset_password"), {"email": "unknown@example.com"})
        self.assertRedirects(response, reverse("account_reset_password_done"))
        email = Email.objects.get()
        self.assertNotIn("/password/reset/key/", email.message)

    def test_admin_preview_requires_mail_view_permission(self):
        call_command("invite_user", "preview@example.com", base_url="http://localhost:8001", stdout=StringIO())
        email = Email.objects.get()
        url = reverse("admin:post_office_email_change", args=[email.pk])
        staff = User.data.create_user(username="mail-viewer", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(url).status_code, 403)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="post_office", codename="view_email"))

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "preview%40example.com")


@override_settings(EMAIL_BACKEND=dev.EMAIL_BACKEND, POST_OFFICE=dev.POST_OFFICE)
class DevelopmentEmailTest(TestCase):
    def test_account_emails_print_immediately_and_remain_in_post_office(self):
        cache.clear()
        user = User.data.create_user(username="console-reset", email="console-reset@example.com")
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        for route, address in (
            ("account_signup", "console-signup@example.com"),
            ("account_reset_password", user.email),
        ):
            with self.subTest(route=route), redirect_stdout(StringIO()) as output:
                response = self.client.post(reverse(route), {"email": address})

                self.assertEqual(response.status_code, 302)
                email = Email.objects.filter(to=[address]).get()
                self.assertEqual(email.status, STATUS.sent)
                self.assertIn(address, output.getvalue())
                printed_body = message_from_string(output.getvalue()).get_payload(decode=True).decode("utf-8")
                self.assertIn(email.message, printed_body)
                if route == "account_signup":
                    self.assertIn(self.client.session["account_email_verification_code"]["code"], output.getvalue())
                else:
                    self.assertIn("/password/reset/key/", printed_body)
