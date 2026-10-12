import hashlib
import json
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from fido2.cose import ES256
from fido2.utils import websafe_encode
from fido2.webauthn import AttestationObject, AttestedCredentialData, AuthenticatorData, CollectedClientData

from users.models import User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasskeySignupTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client.defaults["HTTP_HOST"] = "localhost"
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = b"demo-passkey-test"

    def start_signup(self):
        with patch(
            "allauth.account.adapter.DefaultAccountAdapter.generate_email_verification_code", return_value="123456"
        ):
            response = self.client.post(reverse("account_signup_by_passkey"), {"email": "passkey@example.com"})
        self.assertRedirects(response, reverse("account_email_verification_sent"))
        self.assertEqual(mail.outbox[-1].to, ["passkey@example.com"])
        self.assertIn("123456", mail.outbox[-1].body)
        return User.data.get(email="passkey@example.com")

    def verify_email(self):
        response = self.client.post(reverse("account_email_verification_sent"), {"code": "123456"})
        self.assertRedirects(response, reverse("mfa_signup_webauthn"))
        return self.client.get(reverse("mfa_signup_webauthn")).context["js_data"]["creation_options"]["publicKey"]

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
        user = User.data.create_user(username="password-user", email="password@example.com", password="test-password")
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        self.client.post(reverse("account_login"), {"login": user.email, "password": "test-password"})
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.client.post(reverse("account_logout"))
        for _ in range(settings.AXES_FAILURE_LIMIT):
            self.client.post(reverse("account_login"), {"login": user.email, "password": "wrong-password"})

        self.client.post(reverse("account_login"), {"login": user.email, "password": "test-password"})

        self.assertNotIn("_auth_user_id", self.client.session)
