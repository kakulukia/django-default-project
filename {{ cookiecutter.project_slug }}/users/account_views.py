from allauth.account.forms import SetPasswordForm
from allauth.account.internal.flows.password_change import finalize_password_set
from allauth.mfa.webauthn.forms import SignupWebAuthnForm
from allauth.mfa.webauthn.views import SignupWebAuthnView
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.debug import sensitive_post_parameters


@method_decorator(xframe_options_sameorigin, name="dispatch")
@method_decorator(sensitive_post_parameters("password1", "password2"), name="dispatch")
class SignupCredentialsView(SignupWebAuthnView):
    # Keep allauth's verified-email stage guard for both credential choices.
    def get_form_class(self):
        if self.request.POST.get("method") == "password":
            return SetPasswordForm
        return super().get_form_class()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self._login_stage.login.user
        if self.request.POST.get("method") == "password":
            context["password_form"] = kwargs.get("form", context["form"])
            context["form"] = SignupWebAuthnForm(user=user)
        else:
            context["password_form"] = SetPasswordForm(user=user)
        return context

    def form_valid(self, form):
        if self.request.POST.get("method") == "password":
            if form.user.has_usable_password():
                return self._login_stage.abort()
            form.save()
            finalize_password_set(self.request, form.user)
            return self._login_stage.exit()
        return super().form_valid(form)
