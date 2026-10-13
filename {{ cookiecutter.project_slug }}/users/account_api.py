import json

from allauth.account.forms import SetPasswordForm
from allauth.account.internal.flows.password_change import finalize_password_set
from allauth.core.internal.httpkit import is_headless_request
from allauth.decorators import rate_limit
from allauth.headless.account.inputs import ResendEmailVerificationInput
from allauth.headless.account.views import ManageEmailView as AllauthManageEmailView
from allauth.headless.adapter import DefaultHeadlessAdapter
from allauth.headless.base.response import APIResponse, AuthenticationResponse, ConflictResponse
from allauth.headless.base.views import AuthenticationStageAPIView
from allauth.headless.internal.restkit.inputs import Input
from allauth.headless.mfa.views import ManageTOTPView as AllauthManageTOTPView
from allauth.mfa.adapter import get_adapter as get_mfa_adapter
from allauth.mfa.webauthn.stages import PasskeySignupStage
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator


class UnverifiedEmailInput(ResendEmailVerificationInput):
    def clean_email(self):
        address = super().clean_email()
        if address.verified:
            raise ValidationError("Diese E-Mail-Adresse ist bereits bestätigt.", code="already_verified")
        return address


class ManageEmailView(AllauthManageEmailView):
    input_class = {**AllauthManageEmailView.input_class, "PUT": UnverifiedEmailInput}


class ManageTOTPView(AllauthManageTOTPView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if response.status_code == 404:
            meta = json.loads(response.content)["meta"]
            meta["qr_svg"] = get_mfa_adapter().build_totp_svg(meta["totp_url"])
            return APIResponse(request, meta=meta, status=404)
        return response


class AccountHeadlessAdapter(DefaultHeadlessAdapter):
    def get_frontend_url(self, urlname, **kwargs):
        # Keep standalone account forms usable alongside the JSON dialog.
        if not is_headless_request(self.request):
            return None
        return super().get_frontend_url(urlname, **kwargs)


class SignupPasswordInput(SetPasswordForm, Input):
    pass


@method_decorator(rate_limit(action="signup"), name="handle")
class SignupPasswordView(AuthenticationStageAPIView):
    stage_class = PasskeySignupStage
    input_class = SignupPasswordInput

    def get_input_kwargs(self):
        return {"user": self.stage.login.user}

    def post(self, request, *args, **kwargs):
        user = self.stage.login.user
        if user.has_usable_password():
            return ConflictResponse(request)
        self.input.save()
        finalize_password_set(request, user)
        self.stage.exit()
        return AuthenticationResponse(request)
