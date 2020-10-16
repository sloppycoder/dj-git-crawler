from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="admin/", permanent=False)),
    path("stats/", include("stats.urls")),
    path("admin/", admin.site.urls),
]
