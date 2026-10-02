from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.sites.models import Site
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _
from post_office import mail

from utils.models import BaseModel


class User(AbstractUser, BaseModel):
    data = UserManager()

    class Meta:
        ordering = ["-created"]
        base_manager_name = "data"
        default_manager_name = "data"
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def get_base_url(self):
        site = Site.objects.get_current()
        scheme = "https" if settings.SECURE_SSL_REDIRECT else "http"
        return f"{scheme}://{site.domain}"

    def email_user(self, template_name, context=None):
        if not self.email:
            return

        receiver = self.email
        if settings.EMAIL_OVERRIDE_ADDRESS:
            receiver = settings.EMAIL_OVERRIDE_ADDRESS

        if not context:
            context = {}
        context["user"] = self
        context["base_url"] = self.get_base_url()
        context["footer"] = settings.EMAIL_FOOTER

        activate("de")
        mail.send(
            receiver,
            settings.DEFAULT_FROM_EMAIL,
            template=template_name,
            context=context,
        )
