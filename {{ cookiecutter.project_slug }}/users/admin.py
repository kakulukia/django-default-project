from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from users.models import User

admin.site.enable_nav_sidebar = False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    change_form_template = "loginas/change_form.html"
    readonly_fields = ("created", "modified", "last_login")
    fieldsets = DjangoUserAdmin.fieldsets + ((_("Timestamps"), {"fields": ("created", "modified")}),)
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active", "created")
