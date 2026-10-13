import hashlib
import json
import re
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from fido2.cose import ES256
from fido2.utils import websafe_encode
from fido2.webauthn import AttestationObject, AttestedCredentialData, AuthenticatorData, CollectedClientData

from users.models import User


class WebAuthnCredentialMixin:
    def registration_credential(self, options):
        credential_data = AttestedCredentialData.create(
            bytes(16), self.credential_id, ES256.from_cryptography_key(self.private_key.public_key())
        )
        auth_data = AuthenticatorData.create(
            hashlib.sha256(options["rp"]["id"].encode()).digest(),
            AuthenticatorData.FLAG.UP | AuthenticatorData.FLAG.UV | AuthenticatorData.FLAG.AT,
            0,
            credential_data,
        )
        client_data = CollectedClientData.create("webauthn.create", options["challenge"], "http://localhost")
        return {
            "id": websafe_encode(self.credential_id),
            "rawId": websafe_encode(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": websafe_encode(client_data),
                "attestationObject": websafe_encode(AttestationObject.create("none", auth_data, {})),
            },
            "clientExtensionResults": {"credProps": {"rk": True}},
        }


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailManagementTest(TestCase):
    def setUp(self):
        self.client.defaults["HTTP_HOST"] = "localhost"
        self.user = User.data.create_user(username="email-manager", email="first@example.com")
        self.first = EmailAddress.objects.create(user=self.user, email=self.user.email, primary=True, verified=True)
        self.second = EmailAddress.objects.create(user=self.user, email="second@example.com", verified=True)
        other = User.data.create_user(username="other-email-manager", email="other@example.com")
        self.foreign = EmailAddress.objects.create(user=other, email=other.email, primary=True, verified=True)
        self.client.force_login(self.user)

    def test_each_row_submits_its_own_email_to_native_actions(self):
        response = self.client.get(reverse("account_email"))
        rows = re.findall(r"<form[^>]*data-account-email.*?</form>", response.content.decode(), re.S)
        self.assertEqual(len(rows), 2)
        for row, address in zip(rows, (self.first, self.second), strict=True):
            self.assertInHTML(f'<input type="hidden" name="email" value="{address.email}">', row)
            self.assertIn('name="csrfmiddlewaretoken"', row)
            for action in ("action_send", "action_remove"):
                self.assertIn(f'name="{action}"', row)
            if address.primary:
                self.assertNotIn('name="action_primary"', row)
                self.assertIn('mdi mdi-star"', row)
                self.assertNotIn("mdi-star-outline", row)
            else:
                self.assertIn('name="action_primary"', row)
                self.assertIn("mdi-star-outline", row)
        self.assertNotContains(response, self.foreign.email)

        email = re.search(r'name="email" value="([^"]+)"', rows[1])[1]
        self.client.post(reverse("account_email"), {"email": email, "action_primary": ""})
        self.second.refresh_from_db()
        self.assertTrue(self.second.primary)
        self.client.post(reverse("account_email"), {"email": self.first.email, "action_remove": ""})
        self.assertFalse(EmailAddress.objects.filter(pk=self.first.pk).exists())
        self.assertTrue(EmailAddress.objects.filter(pk=self.second.pk).exists())

    def test_native_actions_protect_primary_and_foreign_addresses(self):
        for address in (self.first, self.foreign):
            self.client.post(reverse("account_email"), {"email": address.email, "action_remove": ""})
            self.assertTrue(EmailAddress.objects.filter(pk=address.pk).exists())
        self.client.post(reverse("account_email"), {"email": self.foreign.email, "action_primary": ""})
        self.first.refresh_from_db()
        self.assertTrue(self.first.primary)

    def test_invalid_add_email_keeps_the_form_and_reports_errors(self):
        response = self.client.post(reverse("account_email"), {"email": "invalid", "action_add": ""})
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)

    def test_last_email_cannot_be_removed_through_the_standalone_form(self):
        self.second.delete()
        self.client.post(reverse("account_email"), {"email": self.first.email, "action_remove": ""})
        self.assertTrue(EmailAddress.objects.filter(pk=self.first.pk).exists())
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, self.first.email)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasskeySignupTest(WebAuthnCredentialMixin, TestCase):
    def setUp(self):
        cache.clear()
        self.client.defaults["HTTP_HOST"] = "localhost"
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = b"demo-passkey-test"

    def start_signup(self):
        with patch(
            "allauth.account.adapter.DefaultAccountAdapter.generate_email_verification_code", return_value="123456"
        ):
            response = self.client.post(reverse("account_signup"), {"email": "passkey@example.com"})
        self.assertRedirects(response, reverse("account_email_verification_sent"))
        self.assertEqual(mail.outbox[-1].to, ["passkey@example.com"])
        self.assertIn("123456", mail.outbox[-1].body)
        return User.data.get(email="passkey@example.com")

    def verify_email(self):
        response = self.client.post(reverse("account_email_verification_sent"), {"code": "123456"})
        self.assertRedirects(response, reverse("mfa_signup_webauthn"))
        return self.client.get(reverse("mfa_signup_webauthn")).context["js_data"]["creation_options"]["publicKey"]

    def test_email_confirmation_then_passkey_signup_and_passwordless_login(self):
        form = self.client.get(reverse("account_signup_by_passkey")).context["form"]
        self.assertEqual(set(form.fields), {"email"})
        user = self.start_signup()
        self.assertFalse(user.has_usable_password())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(EmailAddress.objects.get(user=user).verified)
        self.assertRedirects(
            self.client.get(reverse("mfa_signup_webauthn")), reverse("account_signup"), fetch_redirect_response=False
        )

        options = self.verify_email()
        self.assertTrue(EmailAddress.objects.get(user=user).verified)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(options["authenticatorSelection"]["residentKey"], "required")
        self.assertEqual(options["authenticatorSelection"]["userVerification"], "required")
        credential = self.registration_credential(options)
        user_handle = options["user"]["id"]
        response = self.client.post(
            reverse("mfa_signup_webauthn"), {"name": "Test passkey", "credential": json.dumps(credential)}
        )
        self.assertRedirects(response, "/")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertTrue(Authenticator.objects.get(user=user, type=Authenticator.Type.WEBAUTHN).wrap().is_passwordless)

        self.client.post(reverse("account_logout"))
        options = self.client.get(reverse("mfa_login_webauthn"), HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()[
            "request_options"
        ]["publicKey"]
        auth_data = AuthenticatorData.create(
            hashlib.sha256(options["rpId"].encode()).digest(), AuthenticatorData.FLAG.UP | AuthenticatorData.FLAG.UV, 1
        )
        client_data = CollectedClientData.create("webauthn.get", options["challenge"], "http://localhost")
        signature = self.private_key.sign(auth_data + client_data.hash, ec.ECDSA(hashes.SHA256()))
        assertion = {
            "id": websafe_encode(self.credential_id),
            "rawId": websafe_encode(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": websafe_encode(client_data),
                "authenticatorData": websafe_encode(auth_data),
                "signature": websafe_encode(signature),
                "userHandle": user_handle,
            },
            "clientExtensionResults": {},
        }
        response = self.client.post(reverse("mfa_login_webauthn"), {"credential": json.dumps(assertion)})
        self.assertRedirects(response, "/")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
        self.client.post(reverse("account_logout"))
        self.client.post(reverse("mfa_login_webauthn"), {"credential": json.dumps(assertion)})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_email_and_code_do_not_unlock_passkey_signup(self):
        for email in ("", "not-an-email"):
            with self.subTest(email=email):
                response = self.client.post(reverse("account_signup_by_passkey"), {"email": email})
                self.assertEqual(response.status_code, 200)
                self.assertIn("email", response.context["form"].errors)
        self.assertFalse(User.data.exists())
        user = self.start_signup()
        response = self.client.post(reverse("account_email_verification_sent"), {"code": "000000"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("code", response.context["form"].errors)
        self.assertFalse(EmailAddress.objects.get(user=user).verified)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_choice_is_available_only_after_verification_and_completes_signup(self):
        user = self.start_signup()
        url = reverse("mfa_signup_webauthn")
        password = "Strong-demo-password-492!"
        payload = {"method": "password", "password1": password, "password2": password}
        self.assertRedirects(self.client.post(url, payload), reverse("account_signup"), fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())
        self.assertNotIn("_auth_user_id", self.client.session)

        self.verify_email()
        response = self.client.get(url)
        self.assertContains(response, "Passkey erstellen")
        self.assertContains(response, "Passwort speichern")
        self.assertContains(response, 'data-selected-method="passkey"')
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(self.client.get("/api/users/").status_code, 403)
        for first, second in (("", ""), ("short", "short"), (password, "different-password")):
            with self.subTest(first=first, second=second):
                response = self.client.post(url, {"method": "password", "password1": first, "password2": second})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["password_form"].errors)
                self.assertContains(response, 'data-selected-method="password"')
                self.assertContains(response, 'id="mfa_webauthn_signup"')
                self.assertNotIn("_auth_user_id", self.client.session)
                user.refresh_from_db()
                self.assertFalse(user.has_usable_password())

        response = self.client.post(url, payload)
        self.assertRedirects(response, "/")
        user.refresh_from_db()
        self.assertTrue(user.check_password(password))
        self.assertFalse(Authenticator.objects.filter(user=user).exists())
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.client.post(reverse("account_logout"))
        self.client.post(url, {**payload, "password1": "Replacement-492!", "password2": "Replacement-492!"})
        user.refresh_from_db()
        self.assertTrue(user.check_password(password))
        self.assertNotIn("_auth_user_id", self.client.session)
        response = self.client.post(reverse("account_login"), {"login": user.email, "password": password})
        self.assertRedirects(response, "/")

    def test_credential_setup_requires_current_session_and_csrf(self):
        self.start_signup()
        self.verify_email()
        url = reverse("mfa_signup_webauthn")
        payload = {
            "method": "password",
            "password1": "Strong-demo-password-492!",
            "password2": "Strong-demo-password-492!",
        }
        other_browser = Client(HTTP_HOST="localhost")
        self.assertRedirects(other_browser.post(url, payload), reverse("account_signup"), fetch_redirect_response=False)
        csrf_client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
        csrf_client.cookies = self.client.cookies.copy()
        self.assertEqual(csrf_client.post(url, payload).status_code, 403)
        session = self.client.session
        session["account_login"]["initiated_at"] = 1
        session.save()
        self.assertRedirects(self.client.post(url, payload), reverse("account_signup"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_pending_signup_cannot_replace_a_password_set_elsewhere(self):
        user = self.start_signup()
        self.verify_email()
        user.set_password("Existing-password-492!")
        user.save()
        response = self.client.post(
            reverse("mfa_signup_webauthn"),
            {"method": "password", "password1": "Replacement-492!", "password2": "Replacement-492!"},
        )
        self.assertRedirects(response, reverse("account_login"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("Existing-password-492!"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_anonymous_management_and_malformed_login_are_rejected(self):
        self.assertRedirects(
            self.client.get(reverse("mfa_index")), reverse("account_login") + "?next=" + reverse("mfa_index")
        )
        for credential in ("", "{}", "not-json"):
            with self.subTest(credential=credential):
                response = self.client.post(reverse("mfa_login_webauthn"), {"credential": credential})
                self.assertRedirects(response, reverse("account_login"))
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_unverified_superuser_cannot_add_a_passkey(self):
        user = User.data.create_superuser(username="admin", email="admin@example.com", password="test-password")
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=False)
        self.client.force_login(user)

        response = self.client.get(reverse("mfa_add_webauthn"))

        self.assertRedirects(response, reverse("mfa_index"))
        self.assertFalse(Authenticator.objects.filter(user=user).exists())

    def test_axes_blocks_correct_password_after_failed_email_logins(self):
        response = self.client.get(reverse("account_login"))
        self.assertNotIn("remember", response.context["form"].fields)
        user = User.data.create_user(username="password-user", email="password@example.com", password="test-password")
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        self.client.post(reverse("account_login"), {"login": user.email, "password": "test-password"})
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
        self.client.post(reverse("account_logout"))
        for _ in range(settings.AXES_FAILURE_LIMIT):
            self.client.post(reverse("account_login"), {"login": user.email, "password": "wrong-password"})

        response = self.client.post(reverse("account_login"), {"login": user.email, "password": "test-password"})
        self.assertEqual(response.status_code, 429)
        self.assertTemplateUsed(response, "account/lockout.html")
        self.assertNotIn("_auth_user_id", self.client.session)
