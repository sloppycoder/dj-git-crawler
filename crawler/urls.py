from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path("stats/", include("stats.urls")),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url=admin.site.urls)),
]
