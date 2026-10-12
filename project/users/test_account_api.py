import hashlib
import re
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from allauth.mfa.totp.internal.auth import TOTP, format_hotp_value, generate_totp_secret, hotp_value
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from fido2.utils import websafe_encode
from fido2.webauthn import AuthenticatorData, CollectedClientData

from users.models import User
from users.test_allauth import WebAuthnCredentialMixin


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountAPITest(WebAuthnCredentialMixin, TestCase):
    base = "/_allauth/browser/v1/"
    password = "Strong-demo-password-492!"

    def setUp(self):
        cache.clear()
        self.client.defaults.update(HTTP_HOST="localhost", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = b"headless-test-passkey"

    def api(self, path, method="get", data=None, status=200, client=None):
        client = client or self.client
        response = getattr(client, method)(self.base + path, data=data or {}, content_type="application/json")
        self.assertEqual(response.status_code, status, response.content)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        return response.json()

    def start_signup(self, verify=True):
        with patch(
            "allauth.account.adapter.DefaultAccountAdapter.generate_email_verification_code", return_value="123456"
        ):
            result = self.api("auth/signup", "post", {"email": "api@example.com"}, status=401)
        self.assertIn({"id": "verify_email", "is_pending": True}, result["data"]["flows"])
        self.assertNotIn("_auth_user_id", self.client.session)
        if verify:
            result = self.api("auth/email/verify", "post", {"key": "123456"}, status=401)
            self.assertIn({"id": "mfa_signup_webauthn", "is_pending": True}, result["data"]["flows"])
        return User.data.get(email="api@example.com")

    def test_email_first_password_signup_and_session_login_logout(self):
        for email in ("", "invalid"):
            result = self.api("auth/signup", "post", {"email": email}, status=400)
            self.assertEqual(result["errors"][0]["param"], "email")
        self.assertFalse(User.data.exists())
        user = self.start_signup(verify=False)
        payload = {"password1": self.password, "password2": self.password}
        self.api("auth/signup/password", "post", payload, status=401)
        self.api("auth/email/verify", "post", {"key": "wrong"}, status=400)
        self.assertFalse(EmailAddress.objects.get(user=user).verified)
        self.api("auth/email/verify", "post", {"key": "123456"}, status=401)
        for first, second in (("", ""), ("short", "short"), (self.password, "different")):
            self.api("auth/signup/password", "post", {"password1": first, "password2": second}, status=400)
            self.assertNotIn("_auth_user_id", self.client.session)
        result = self.api("auth/signup/password", "post", payload)
        self.assertTrue(result["meta"]["is_authenticated"])
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.password))
        self.api("auth/session", "delete", status=401)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.api("auth/login", "post", {"email": user.email, "password": "wrong"}, status=400)
        result = self.api("auth/login", "post", {"username": user.username, "password": self.password})
        self.assertTrue(result["meta"]["is_authenticated"])
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

    def test_signup_stage_requires_verified_current_session_csrf_and_timeout(self):
        user = self.start_signup()
        payload = {"password1": self.password, "password2": self.password}
        other = Client(HTTP_HOST="localhost")
        self.api("auth/signup/password", "post", payload, status=401, client=other)
        csrf_client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
        csrf_client.cookies = self.client.cookies.copy()
        self.assertEqual(csrf_client.post(self.base + "auth/signup/password", payload).status_code, 403)
        token = csrf_client.cookies["csrftoken"].value
        response = csrf_client.post(
            self.base + "auth/signup/password",
            {"password1": "short", "password2": "short"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 400)
        session = self.client.session
        session["account_login"]["initiated_at"] = 1
        session.save()
        self.api("auth/signup/password", "post", payload, status=401)
        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())

    def test_pending_stage_cannot_replace_an_existing_password(self):
        user = self.start_signup()
        user.set_password(self.password)
        user.save()
        self.api(
            "auth/signup/password",
            "post",
            {"password1": "Replacement-492!", "password2": "Replacement-492!"},
            status=409,
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.password))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_passkey_signup_login_and_replay_protection(self):
        user = self.start_signup()
        options = self.api("auth/webauthn/signup")["data"]["creation_options"]["publicKey"]
        credential = self.registration_credential(options)
        result = self.api("auth/webauthn/signup", "put", {"name": "REST passkey", "credential": credential})
        self.assertTrue(result["meta"]["is_authenticated"])
        self.assertTrue(Authenticator.objects.get(user=user, type=Authenticator.Type.WEBAUTHN).wrap().is_passwordless)
        self.api("auth/session", "delete", status=401)
        options_login = self.api("auth/webauthn/login")["data"]["request_options"]["publicKey"]
        auth_data = AuthenticatorData.create(
            hashlib.sha256(options_login["rpId"].encode()).digest(),
            AuthenticatorData.FLAG.UP | AuthenticatorData.FLAG.UV,
            1,
        )
        client_data = CollectedClientData.create("webauthn.get", options_login["challenge"], "http://localhost")
        assertion = {
            "id": websafe_encode(self.credential_id),
            "rawId": websafe_encode(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": websafe_encode(client_data),
                "authenticatorData": websafe_encode(auth_data),
                "signature": websafe_encode(
                    self.private_key.sign(auth_data + client_data.hash, ec.ECDSA(hashes.SHA256()))
                ),
                "userHandle": options["user"]["id"],
            },
            "clientExtensionResults": {},
        }
        result = self.api("auth/webauthn/login", "post", {"credential": assertion})
        self.assertTrue(result["meta"]["is_authenticated"])
        self.api("auth/session", "delete", status=401)
        self.api("auth/webauthn/login", "post", {"credential": assertion}, status=400)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_login_with_passwordless_passkey_does_not_require_second_factor(self):
        user = self.start_signup()
        user.set_password(self.password)
        user.save()
        options = self.api("auth/webauthn/signup")["data"]["creation_options"]["publicKey"]
        self.api(
            "auth/webauthn/signup", "put", {"name": "Passkey", "credential": self.registration_credential(options)}
        )
        self.api("auth/session", "delete", status=401)

        for recovery_codes in (False, True):
            with self.subTest(recovery_codes=recovery_codes):
                if recovery_codes:
                    Authenticator.objects.create(user=user, type=Authenticator.Type.RECOVERY_CODES, data={})
                result = self.api("auth/login", "post", {"username": user.username, "password": self.password})
                self.assertTrue(result["meta"]["is_authenticated"])
                self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
                self.api("auth/session", "delete", status=401)
                headed = Client(HTTP_HOST="localhost")
                response = headed.post("/accounts/login/", {"login": user.username, "password": self.password})
                self.assertRedirects(response, "/", fetch_redirect_response=False)
                self.assertEqual(headed.session["_auth_user_id"], str(user.pk))

    def test_explicit_second_factors_still_block_password_login(self):
        user = self.start_signup()
        user.set_password(self.password)
        user.save()
        options = self.api("auth/webauthn/signup")["data"]["creation_options"]["publicKey"]
        self.api(
            "auth/webauthn/signup", "put", {"name": "Passkey", "credential": self.registration_credential(options)}
        )
        key = Authenticator.objects.get(user=user, type=Authenticator.Type.WEBAUTHN)
        self.api("auth/session", "delete", status=401)
        secret = generate_totp_secret()
        totp = TOTP.activate(user, secret)

        for method in ("totp", "security_key", "legacy_key"):
            with self.subTest(method=method):
                if method == "security_key":
                    totp.instance.delete()
                    key.data["credential"]["clientExtensionResults"]["credProps"]["rk"] = False
                    key.save()
                elif method == "legacy_key":
                    key.data["credential"]["clientExtensionResults"] = {}
                    key.save()
                result = self.api(
                    "auth/login", "post", {"username": user.username, "password": self.password}, status=401
                )
                pending = next(flow for flow in result["data"]["flows"] if flow.get("is_pending"))
                self.assertEqual(pending["id"], "mfa_authenticate")
                self.assertNotIn("_auth_user_id", self.client.session)
                self.api("auth/2fa/authenticate", "post", {"code": "invalid"}, status=400)
                self.assertNotIn("_auth_user_id", self.client.session)
                if method == "totp":
                    with patch(
                        "allauth.mfa.totp.internal.auth.yield_hotp_counters_from_time", return_value=iter([12345])
                    ):
                        code = format_hotp_value(hotp_value(secret, 12345))
                        result = self.api("auth/2fa/authenticate", "post", {"code": code})
                    self.assertTrue(result["meta"]["is_authenticated"])
                self.api("auth/session", "delete", status=401)
                headed = Client(HTTP_HOST="localhost")
                response = headed.post("/accounts/login/", {"login": user.username, "password": self.password})
                self.assertRedirects(response, reverse("mfa_authenticate"), fetch_redirect_response=False)
                self.assertNotIn("_auth_user_id", headed.session)

    def test_email_management_checks_ownership_primary_and_invalid_input(self):
        self.api("account/email", status=401)
        user = self.start_signup()
        self.api("auth/signup/password", "post", {"password1": self.password, "password2": self.password})
        first = EmailAddress.objects.get(user=user)
        second = EmailAddress.objects.create(user=user, email="secondary@example.com", verified=True)
        other = User.data.create_user(username="foreign", email="foreign@example.com")
        EmailAddress.objects.create(user=other, email=other.email, verified=True, primary=True)
        result = self.api("account/email")
        self.assertEqual({item["email"] for item in result["data"]}, {first.email, second.email})
        self.api("account/email", "delete", {"email": first.email}, status=400)
        self.api("account/email", "delete", {"email": other.email}, status=400)
        self.api("account/email", "patch", {"email": other.email, "primary": True}, status=400)
        self.api("account/email", "post", {"email": "invalid"}, status=400)
        self.api("account/email", "patch", {"email": second.email, "primary": True})
        second.refresh_from_db()
        self.assertTrue(second.primary)
        self.api("account/email", "delete", {"email": first.email})
        self.assertFalse(EmailAddress.objects.filter(pk=first.pk).exists())

    def test_verified_email_cannot_start_another_verification(self):
        user = self.start_signup()
        self.api("auth/signup/password", "post", {"password1": self.password, "password2": self.password})
        address = EmailAddress.objects.get(user=user)
        mail.outbox.clear()
        result = self.api("account/email", "put", {"email": address.email}, status=400)
        self.assertEqual(result["errors"][0]["code"], "already_verified")
        self.assertNotIn("account_email_verification_code", self.client.session)
        self.assertEqual(mail.outbox, [])
        self.assertEqual(len(self.api("account/email")["data"]), 1)
        address.refresh_from_db()
        self.assertTrue(address.verified)
        self.assertTrue(address.primary)

        address.verified = False
        address.save(update_fields=["verified"])
        cache.clear()
        self.api("account/email", "put", {"email": address.email})
        self.assertIn("account_email_verification_code", self.client.session)
        self.assertEqual(len(mail.outbox), 1)

    def test_last_email_cannot_be_removed_and_login_still_works(self):
        user = self.start_signup()
        self.api("auth/signup/password", "post", {"password1": self.password, "password2": self.password})
        address = EmailAddress.objects.get(user=user)
        for verified in (True, False):
            address.verified = verified
            address.save(update_fields=["verified"])
            self.api("account/email", "delete", {"email": address.email}, status=400)
            self.assertTrue(EmailAddress.objects.filter(pk=address.pk).exists())
        address.verified = True
        address.save(update_fields=["verified"])
        user.refresh_from_db()
        self.assertEqual(user.email, address.email)
        mail.outbox.clear()
        self.api("auth/session", "delete", status=401)
        result = self.api("auth/login", "post", {"username": user.username, "password": self.password})
        self.assertTrue(result["meta"]["is_authenticated"])
        self.assertNotIn("account_email_verification_code", self.client.session)
        self.assertEqual(mail.outbox, [])

    def test_last_verified_email_is_kept_when_an_unverified_primary_exists(self):
        user = self.start_signup()
        self.api("auth/signup/password", "post", {"password1": self.password, "password2": self.password})
        address = EmailAddress.objects.get(user=user)
        address.primary = False
        address.save(update_fields=["primary"])
        EmailAddress.objects.create(user=user, email="unverified@example.com", primary=True)
        self.api("account/email", "delete", {"email": address.email}, status=400)
        self.assertTrue(EmailAddress.objects.filter(pk=address.pk, verified=True).exists())

    def test_totp_setup_activation_login_and_deactivation(self):
        endpoint = "account/authenticators/totp"
        anonymous = self.api(endpoint, status=401)
        self.assertNotIn("secret", anonymous.get("meta", {}))
        user = self.start_signup()
        self.api("auth/signup/password", "post", {"password1": self.password, "password2": self.password})
        setup = self.api(endpoint, status=404)["meta"]
        self.assertIn("<svg", setup["qr_svg"])
        self.assertIn("<path", setup["qr_svg"])
        self.assertIn(setup["secret"], setup["totp_url"])
        self.assertFalse(Authenticator.objects.filter(user=user, type=Authenticator.Type.TOTP).exists())
        for invalid in ("", "invalid", "123456789"):
            self.api(endpoint, "post", {"code": invalid}, status=400)
        self.assertFalse(Authenticator.objects.filter(user=user, type=Authenticator.Type.TOTP).exists())
        with patch("allauth.mfa.totp.internal.auth.yield_hotp_counters_from_time", return_value=iter([12345])):
            self.api(endpoint, "post", {"code": format_hotp_value(hotp_value(setup["secret"], 12345))}, status=401)
        self.assertFalse(Authenticator.objects.filter(user=user, type=Authenticator.Type.TOTP).exists())
        self.api("auth/reauthenticate", "post", {"password": self.password})
        with patch("allauth.mfa.totp.internal.auth.yield_hotp_counters_from_time", return_value=iter([12345])):
            self.api(endpoint, "post", {"code": format_hotp_value(hotp_value(setup["secret"], 12345))})
        self.assertEqual(self.api(endpoint)["data"]["type"], "totp")
        self.assertIn("unused_codes", self.api("account/authenticators/recovery-codes")["data"])
        self.api("auth/session", "delete", status=401)
        login = self.api("auth/login", "post", {"username": user.username, "password": self.password}, status=401)
        self.assertIn("totp", next(flow for flow in login["data"]["flows"] if flow.get("is_pending"))["types"])
        self.assertNotIn("_auth_user_id", self.client.session)
        with patch("allauth.mfa.totp.internal.auth.yield_hotp_counters_from_time", return_value=iter([12346])):
            self.api("auth/2fa/authenticate", "post", {"code": format_hotp_value(hotp_value(setup["secret"], 12346))})
        self.api(endpoint, "delete")
        self.assertFalse(Authenticator.objects.filter(user=user, type=Authenticator.Type.TOTP).exists())
        self.api("auth/session", "delete", status=401)
        self.api("auth/login", "post", {"username": user.username, "password": self.password})

    def test_password_reset_json_link_validation_and_single_use(self):
        user = User.data.create_user(username="reset-api", email="reset-api@example.com", password=self.password)
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        for email in (user.email, "unknown@example.com"):
            self.api("auth/password/request", "post", {"email": email})
        body = mail.outbox[0].body
        url = re.search(r"http://localhost/\?account=reset&key=\S+", body).group()
        key = parse_qs(urlsplit(url).query)["key"][0]
        response = self.client.get(self.base + "auth/password/reset", HTTP_X_PASSWORD_RESET_KEY=key)
        self.assertEqual(response.status_code, 200)
        self.api("auth/password/reset", "post", {"key": key, "password": "short"}, status=400)
        self.api("auth/password/reset", "post", {"key": key, "password": "Replacement-492!"}, status=401)
        self.api("auth/password/reset", "post", {"key": key, "password": self.password}, status=400)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Replacement-492!"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_axes_lockout_remains_json_and_blocks_correct_password(self):
        user = User.data.create_user(username="locked-api", email="locked-api@example.com", password=self.password)
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        for _ in range(settings.AXES_FAILURE_LIMIT):
            self.client.post(
                self.base + "auth/login", {"email": user.email, "password": "wrong"}, content_type="application/json"
            )
        response = self.client.post(
            self.base + "auth/login", {"email": user.email, "password": self.password}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_browser_api_sets_csrf_and_app_token_api_is_disabled(self):
        self.api("auth/session", status=401)
        self.assertIn("csrftoken", self.client.cookies)
        self.assertEqual(self.client.get("/_allauth/app/v1/auth/session").status_code, 404)
        self.assertNotContains(self.client.get("/"), "iframe")

    def test_passkey_management_requires_owner_and_recent_authentication(self):
        user = self.start_signup()
        user.set_password(self.password)
        user.save()
        options = self.api("auth/webauthn/signup")["data"]["creation_options"]["publicKey"]
        self.api(
            "auth/webauthn/signup", "put", {"name": "Own key", "credential": self.registration_credential(options)}
        )
        own = Authenticator.objects.get(user=user, type=Authenticator.Type.WEBAUTHN)
        self.api("auth/reauthenticate", "post", {"password": "wrong"}, status=400)
        self.api("auth/reauthenticate", "post", {"password": self.password})
        other = User.data.create_user(username="foreign-key", email="foreign-key@example.com")
        foreign = Authenticator.objects.create(user=other, type=own.type, data=own.data.copy())
        self.assertEqual([item["id"] for item in self.api("account/authenticators")["data"]], [own.pk])
        self.api("account/authenticators/webauthn", "put", {"id": foreign.pk, "name": "Changed"}, status=400)
        self.api("account/authenticators/webauthn", "delete", {"authenticators": [foreign.pk]}, status=400)
        self.api("account/authenticators/webauthn", "put", {"id": own.pk, "name": "Renamed"})
        own.refresh_from_db()
        self.assertEqual(own.wrap().name, "Renamed")
        with override_settings(ACCOUNT_REAUTHENTICATION_TIMEOUT=-1):
            result = self.api("account/authenticators/webauthn", "delete", {"authenticators": [own.pk]}, status=401)
            self.assertTrue(result["meta"]["is_authenticated"])
            self.api("account/authenticators/recovery-codes", "post", status=401)
        self.assertTrue(Authenticator.objects.filter(pk=own.pk).exists())
        self.assertTrue(Authenticator.objects.filter(pk=foreign.pk).exists())
        codes = self.api("account/authenticators/recovery-codes", "post")["data"]["unused_codes"]
        self.assertTrue(codes)
        self.api("account/authenticators/webauthn", "delete", {"authenticators": [own.pk]})
        self.assertFalse(Authenticator.objects.filter(pk=own.pk).exists())
        self.assertTrue(Authenticator.objects.filter(pk=foreign.pk).exists())

    def test_added_email_requires_code_and_malformed_passkey_is_rejected(self):
        user = self.start_signup()
        self.api("auth/webauthn/signup", "put", {"name": "Invalid key", "credential": {}}, status=400)
        self.assertFalse(Authenticator.objects.filter(user=user).exists())
        self.api("auth/signup/password", "post", {"password1": self.password, "password2": self.password})
        with patch(
            "allauth.account.adapter.DefaultAccountAdapter.generate_email_verification_code", return_value="654321"
        ):
            self.api("account/email", "post", {"email": "added@example.com"})
        self.api("auth/email/verify", "post", {"key": "wrong"}, status=400)
        self.assertFalse(EmailAddress.objects.filter(user=user, email="added@example.com", verified=True).exists())
        self.api("auth/email/verify", "post", {"key": "654321"})
        self.assertTrue(EmailAddress.objects.get(user=user, email="added@example.com").verified)
