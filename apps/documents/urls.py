from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.DocumentBrowserView.as_view(), name="browser"),
]
