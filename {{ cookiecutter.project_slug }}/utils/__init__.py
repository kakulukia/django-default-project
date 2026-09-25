from rest_framework import permissions
from rest_framework.renderers import BrowsableAPIRenderer


class NoFormBrowsableAPIRenderer(BrowsableAPIRenderer):
    """Renders the browsable api, but excludes the forms."""

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        ctx["display_edit_forms"] = False
        return ctx

    def show_form_for_method(self, view, method, request, obj):
        """We never want to do this! So just return False."""
        return False

    def get_rendered_html_form(self, data, view, method, request):
        """Why render _any_ forms at all. This method should return
        rendered HTML, so let's simply return an empty string.
        """
        return ""


class IsOwnerOrSuperAdmin(permissions.BasePermission):
    owner_mapping = {
        "User": "self",
        "YourModel": "user",
        # add new classes and their owner attribute here
    }

    def has_object_permission(self, request, view, obj):
        # Lesezugriffe sind immer erlaubt.
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        owner_field = self.owner_mapping.get(obj.__class__.__name__)
        if not owner_field:
            # If the object is not defined in our mapping, we deny access.
            return False

        owner = obj if owner_field == "self" else getattr(obj, owner_field, None)
        # Allow access if the owner matches the request user or the request user is a superuser.
        return owner == request.user
