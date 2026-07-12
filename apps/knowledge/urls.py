from django.urls import path

from . import views

app_name = "knowledge"

urlpatterns = [
    path("", views.InfothekView.as_view(), name="infothek"),

    path("versand/neu/", views.ShippingOptionCreateView.as_view(), name="shipping_create"),
    path("versand/<int:pk>/", views.ShippingOptionUpdateView.as_view(), name="shipping_update"),
    path("versand/<int:pk>/loeschen/", views.ShippingOptionDeleteView.as_view(), name="shipping_delete"),

    path("zoll/neu/", views.TariffCodeCreateView.as_view(), name="tariff_create"),
    path("zoll/<int:pk>/", views.TariffCodeUpdateView.as_view(), name="tariff_update"),
    path("zoll/<int:pk>/loeschen/", views.TariffCodeDeleteView.as_view(), name="tariff_delete"),

    path(
        "verpackungslizenz/dokumente/neu/",
        views.PackagingLicenseDocumentCreateView.as_view(), name="license_document_create",
    ),
    path(
        "verpackungslizenz/dokumente/<int:pk>/loeschen/",
        views.PackagingLicenseDocumentDeleteView.as_view(), name="license_document_delete",
    ),
    path(
        "verpackungslizenz/meldungen/<int:pk>/bestaetigen/",
        views.PackagingLicenseSubmissionConfirmView.as_view(), name="license_submission_confirm",
    ),
    path(
        "verpackungslizenz/meldungen/<int:pk>/umschalten/",
        views.PackagingLicenseSubmissionToggleView.as_view(), name="license_submission_toggle",
    ),
    path(
        "verpackungslizenz/datenmeldungen/<int:pk>/loeschen/",
        views.PackagingLicenseDataReportDeleteView.as_view(), name="license_data_report_delete",
    ),
    path(
        "verpackungslizenz/datenmeldungen/<int:pk>/ansehen/",
        views.PackagingLicenseDataReportDetailModalView.as_view(), name="license_data_report_detail",
    ),
    path(
        "verpackungslizenz/datenmeldungen/neu/",
        views.PackagingLicenseDataReportCreateView.as_view(), name="license_data_report_create",
    ),
]
