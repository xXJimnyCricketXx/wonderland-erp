from django.urls import path

from . import views

app_name = "wishlist"

urlpatterns = [
    path("", views.WishlistBoardView.as_view(), name="board"),
    path("neu/", views.WishlistItemModalView.as_view(), name="item_create"),
    path("<int:pk>/", views.WishlistItemModalView.as_view(), name="item_update"),
    path("<int:pk>/ansehen/", views.WishlistItemDetailModalView.as_view(), name="item_detail"),
    path("<int:pk>/loeschen/", views.WishlistItemDeleteView.as_view(), name="item_delete"),
]
