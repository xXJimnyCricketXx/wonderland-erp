from django.urls import path

from . import views

app_name = "shopping_list"

urlpatterns = [
    path("", views.ShoppingListView.as_view(), name="list"),
    path("neu/", views.ShoppingListItemCreateView.as_view(), name="create"),
    path("<int:pk>/bearbeiten/", views.ShoppingListItemUpdateView.as_view(), name="update"),
    path("<int:pk>/loeschen/", views.ShoppingListItemArchiveView.as_view(), name="delete"),
]
