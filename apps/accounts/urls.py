from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.ProfileView.as_view(), name="profile"),
    path("passwort/", views.ProfilePasswordChangeView.as_view(), name="profile_password"),
    path("bild/", views.ProfileAvatarView.as_view(), name="profile_avatar"),
]
