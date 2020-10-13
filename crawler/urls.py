from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("stats/", include("stats.urls")),
    path("admin/", admin.site.urls),
]
