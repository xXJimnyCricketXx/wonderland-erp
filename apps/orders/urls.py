from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("neu/", views.OrderCreateView.as_view(), name="create"),
    path("<int:pk>/", views.OrderUpdateView.as_view(), name="update"),
    path("<int:pk>/ansehen/", views.OrderDetailModalView.as_view(), name="detail"),
    path("<int:pk>/archivieren/", views.OrderArchiveView.as_view(), name="archive"),
]
