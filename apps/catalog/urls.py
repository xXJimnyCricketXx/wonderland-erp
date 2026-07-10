from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.ArticleListView.as_view(), name="list"),
    path("neu/", views.ArticleCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ArticleUpdateView.as_view(), name="update"),
    path("<int:pk>/ansehen/", views.ArticleDetailModalView.as_view(), name="detail"),
    path("<int:pk>/archivieren/", views.ArticleArchiveView.as_view(), name="archive"),
]
