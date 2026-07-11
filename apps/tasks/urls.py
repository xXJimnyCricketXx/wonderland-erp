from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.TaskBoardView.as_view(), name="board"),
    path("neu/", views.TaskCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TaskUpdateView.as_view(), name="update"),
    path("<int:pk>/status/", views.TaskStatusUpdateView.as_view(), name="status_update"),
    path("<int:pk>/archivieren/", views.TaskArchiveView.as_view(), name="archive"),
]
