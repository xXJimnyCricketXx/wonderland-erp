from django.urls import path

from . import views

app_name = "data_import"

urlpatterns = [
    path("", views.ImportView.as_view(), name="index"),
    path("artikel/", views.ArticleImportView.as_view(), name="article_import"),
    path("bestellungen/", views.OrderImportView.as_view(), name="order_import"),
    path("bestellungen/positionen/", views.OrderItemImportView.as_view(), name="order_item_import"),
    path("bewertungen/", views.ReviewImportView.as_view(), name="review_import"),
    path("verpackungslizenz/", views.PackagingLicenseXmlImportView.as_view(), name="packaging_license_xml_import"),
    path("statement/", views.StatementImportView.as_view(), name="statement_import"),
]
