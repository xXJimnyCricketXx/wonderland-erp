from django.urls import path

from . import views

app_name = "data_import"

urlpatterns = [
    path("", views.ImportView.as_view(), name="index"),
]
