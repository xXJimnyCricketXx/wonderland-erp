from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [
    path("", views.ContactListView.as_view(), name="list"),
    path("kunden/neu/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("kunden/<int:pk>/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("kunden/<int:pk>/ansehen/", views.CustomerDetailModalView.as_view(), name="customer_detail"),
    path("kunden/<int:pk>/archivieren/", views.CustomerArchiveView.as_view(), name="customer_archive"),
    path("lieferanten/neu/", views.SupplierModalView.as_view(), name="supplier_create"),
    path("lieferanten/<int:pk>/", views.SupplierModalView.as_view(), name="supplier_update"),
    path("lieferanten/<int:pk>/ansehen/", views.SupplierDetailModalView.as_view(), name="supplier_detail"),
    path("lieferanten/<int:pk>/archivieren/", views.SupplierArchiveView.as_view(), name="supplier_archive"),
]
