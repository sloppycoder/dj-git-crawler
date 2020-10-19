from django.urls import path

from . import views

urlpatterns = [
    path("job", views.job, name="job"),
]
