from django.urls import path

from . import views

urlpatterns = [
    path("discover", views.discover, name="discover"),
    path("scan", views.scan, name="scan"),
]
