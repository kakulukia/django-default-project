from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from sample_app.views import index

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__reload__/", include("django_browser_reload.urls")),
        path(r"__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
