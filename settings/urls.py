from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from sample_app.views import index
from users.views import UserViewSet

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    # admin urls
    path("admin/", include("loginas.urls")),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    # application urls
    path("", index),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path(r"__debug__/", include(debug_toolbar.urls)),
        path("__reload__/", include("django_browser_reload.urls")),
    ] + urlpatterns
