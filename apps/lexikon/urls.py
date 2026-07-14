from django.urls import path

from . import views

app_name = "lexikon"

urlpatterns = [
    path("neu/", views.GemstoneCreateView.as_view(), name="gemstone_create"),
    path("<int:pk>/", views.GemstoneUpdateView.as_view(), name="gemstone_update"),
    path("<int:pk>/ansehen/", views.GemstoneDetailModalView.as_view(), name="gemstone_detail"),
    path("<int:pk>/loeschen/", views.GemstoneDeleteView.as_view(), name="gemstone_delete"),
    path("<int:pk>/bild/", views.GemstoneImageView.as_view(), name="gemstone_image"),
]
