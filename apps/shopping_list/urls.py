from django.urls import path

from . import views

app_name = "shopping_list"

urlpatterns = [
    path("", views.ShoppingListView.as_view(), name="list"),
    path("neu/", views.ShoppingListItemModalView.as_view(), name="create"),
    path("<int:pk>/bearbeiten/", views.ShoppingListItemModalView.as_view(), name="update"),
    path("<int:pk>/ansehen/", views.ShoppingListItemDetailModalView.as_view(), name="detail"),
    path("<int:pk>/loeschen/", views.ShoppingListItemArchiveView.as_view(), name="delete"),
]
