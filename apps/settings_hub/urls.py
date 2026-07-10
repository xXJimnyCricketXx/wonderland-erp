from django.urls import path

from . import views

app_name = "settings_hub"

urlpatterns = [
    path("", views.SettingsView.as_view(), name="index"),
    path("referenzdaten/hinzufuegen/", views.ReferenceOptionAddView.as_view(), name="reference_add"),
    path("referenzdaten/<int:pk>/loeschen/", views.ReferenceOptionDeleteView.as_view(), name="reference_delete"),
    path("papierkorb/<slug:slug>/<int:pk>/wiederherstellen/", views.TrashRestoreView.as_view(), name="trash_restore"),
    path("papierkorb/<slug:slug>/<int:pk>/loeschen/", views.TrashHardDeleteView.as_view(), name="trash_hard_delete"),
    path("papierkorb/<slug:slug>/leeren/", views.TrashEmptyView.as_view(), name="trash_empty"),
    path("backups/erstellen/", views.BackupCreateView.as_view(), name="backup_create"),
    path("backups/einstellungen/", views.BackupSettingsUpdateView.as_view(), name="backup_settings"),
    path("backups/<str:filename>/herunterladen/", views.BackupDownloadView.as_view(), name="backup_download"),
    path("backups/<str:filename>/loeschen/", views.BackupDeleteView.as_view(), name="backup_delete"),
    path("danger-zone/datenbank-zuruecksetzen/", views.DatabaseResetView.as_view(), name="database_reset"),
]
