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
    path("danger-zone/bestellungen-loeschen/", views.OrderResetView.as_view(), name="order_reset"),
    path("danger-zone/artikel-loeschen/", views.ArticleResetView.as_view(), name="article_reset"),
    path("verpackungsarten/neu/", views.PackagingTypeCreateView.as_view(), name="packaging_type_create"),
    path("verpackungsarten/<int:pk>/bearbeiten/", views.PackagingTypeUpdateView.as_view(), name="packaging_type_update"),
    path("verpackungsarten/<int:pk>/loeschen/", views.PackagingTypeDeleteView.as_view(), name="packaging_type_delete"),
    path("materialkategorien/neu/", views.MaterialCategoryCreateView.as_view(), name="material_category_create"),
    path("materialkategorien/<int:pk>/bearbeiten/", views.MaterialCategoryUpdateView.as_view(), name="material_category_update"),
    path("materialkategorien/<int:pk>/loeschen/", views.MaterialCategoryDeleteView.as_view(), name="material_category_delete"),
    path("skr03-konten/neu/", views.SKR03AccountCreateView.as_view(), name="skr03_account_create"),
    path("skr03-konten/<int:pk>/bearbeiten/", views.SKR03AccountUpdateView.as_view(), name="skr03_account_update"),
    path("skr03-konten/<int:pk>/loeschen/", views.SKR03AccountDeleteView.as_view(), name="skr03_account_delete"),
    path("konten-zuordnungen/neu/", views.AccountMappingCreateView.as_view(), name="account_mapping_create"),
    path("konten-zuordnungen/<int:pk>/bearbeiten/", views.AccountMappingUpdateView.as_view(), name="account_mapping_update"),
    path("konten-zuordnungen/<int:pk>/loeschen/", views.AccountMappingDeleteView.as_view(), name="account_mapping_delete"),
]
