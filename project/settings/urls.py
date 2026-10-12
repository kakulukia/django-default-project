from allauth.account.views import SignupByPasskeyView
from allauth.headless.constants import Client
from allauth.headless.mfa.views import SignupWebAuthnView
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import TemplateView
from rest_framework import routers

from users.account_api import ManageEmailView, ManageTOTPView, SignupPasswordView
from users.account_views import SignupCredentialsView
from users.views import UserViewSet

handler500 = "utils.views.server_error"

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    # admin urls
    path("admin/", include("loginas.urls")),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("_allauth/browser/v1/auth/signup", SignupWebAuthnView.as_api_view(client=Client.BROWSER)),
    path("_allauth/browser/v1/auth/signup/password", SignupPasswordView.as_api_view(client=Client.BROWSER)),
    path("_allauth/browser/v1/account/email", ManageEmailView.as_api_view(client=Client.BROWSER)),
    path("_allauth/browser/v1/account/authenticators/totp", ManageTOTPView.as_api_view(client=Client.BROWSER)),
    path("_allauth/", include("allauth.headless.urls")),
    path("accounts/signup/", SignupByPasskeyView.as_view(template_name="account/signup.html")),
    path("accounts/2fa/webauthn/signup/", SignupCredentialsView.as_view()),
    path("accounts/", include("allauth.urls")),
    # application urls
    path("", xframe_options_sameorigin(TemplateView.as_view(template_name="index.pug")), name="demo"),
]

if settings.DEBUG:
    import debug_toolbar

    from utils.views import server_error

    urlpatterns = [
        path(r"__debug__/", include(debug_toolbar.urls)),
        path("__reload__/", include("django_browser_reload.urls")),
        path("500/", server_error),  # test url - please remove later
    ] + urlpatterns
