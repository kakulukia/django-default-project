from allauth.account import app_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from allauth.mfa.stages import AuthenticateStage


class AccountAdapter(DefaultAccountAdapter):
    def can_delete_email(self, email_address):
        if not super().can_delete_email(email_address):
            return False
        if email_address.pk and app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
            # Username login still needs a deliverable address for mandatory verification.
            others = EmailAddress.objects.filter(user_id=email_address.user_id).exclude(pk=email_address.pk)
            if email_address.verified:
                others = others.filter(verified=True)
            return others.exists()
        return True

    def get_login_stages(self):
        return [
            "users.account_adapter.ExplicitMFAStage" if stage == "allauth.mfa.stages.AuthenticateStage" else stage
            for stage in super().get_login_stages()
        ]


class ExplicitMFAStage(AuthenticateStage):
    def _should_handle(self, request):
        if not super()._should_handle(request):
            return False
        # Passwordless passkeys are alternative logins, not an opt-in to a second factor.
        authenticators = Authenticator.objects.filter(
            user=self.login.user, type__in=[Authenticator.Type.TOTP, Authenticator.Type.WEBAUTHN]
        )
        return any(
            authenticator.type == Authenticator.Type.TOTP or not authenticator.wrap().is_passwordless
            for authenticator in authenticators
        )
