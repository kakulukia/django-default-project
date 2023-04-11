from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.sites.models import Site
from django.core import validators
from django.db import models
from django.utils.timezone import now
from django.utils.translation import activate
from django.utils.translation import gettext_lazy as _
from django_undeletable.models import BaseModel, UserDataManager
from post_office import mail


class User(AbstractBaseUser, BaseModel, PermissionsMixin):
    username = models.CharField(
        _("username"),
        max_length=30,
        unique=True,
        help_text=_("user.login.username_help"),
        validators=[
            validators.RegexValidator(
                r"^[\w.@+-]+$",
                _("forms.errors.enter_valid_username."),
                "username_invalid",
            )
        ],
    )
    first_name = models.CharField(_("first name"), max_length=30, blank=True)
    last_name = models.CharField(_("last name"), max_length=30, blank=True)
    email = models.EmailField(_("email address"), blank=False)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as "
            "active. Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=now)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    data = UserDataManager()

    class Meta(BaseModel.Meta):
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between."""
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def email_user(self, template_name, context=None):
        """
        Sends an email to this User.
        If settings.EMAIL_OVERRIDE_ADDRESS is set, this mail will be
        redirected to the alternate mail address.

        """
        receiver = self.email
        if settings.EMAIL_OVERRIDE_ADDRESS:
            receiver = settings.EMAIL_OVERRIDE_ADDRESS

        if not context:
            context = {}
        context["user"] = self
        context["base_url"] = "http://{}".format(Site.objects.get_current())
        context["footer"] = settings.EMAIL_FOOTER

        activate("de")
        mail.send(
            receiver,
            settings.DEFAULT_FROM_EMAIL,
            template=template_name,
            context=context,
        )
