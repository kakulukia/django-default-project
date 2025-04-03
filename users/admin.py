from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User

admin.site.enable_nav_sidebar = False


@admin.register(User)
class UserAdmin(UserAdmin):
    change_form_template = "loginas/change_form.html"
