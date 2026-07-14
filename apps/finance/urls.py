from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.FinanceView.as_view(), name="index"),
    path("einnahmen/neu/", views.IncomeCreateView.as_view(), name="income_create"),
    path("einnahmen/<int:pk>/ansehen/", views.IncomeDetailModalView.as_view(), name="income_detail"),
    path("einnahmen/<int:pk>/bearbeiten/", views.IncomeUpdateView.as_view(), name="income_update"),
    path("einnahmen/<int:pk>/loeschen/", views.IncomeArchiveView.as_view(), name="income_archive"),
    path("ausgaben/neu/", views.ExpenseCreateView.as_view(), name="expense_create"),
    path("ausgaben/<int:pk>/ansehen/", views.ExpenseDetailModalView.as_view(), name="expense_detail"),
    path("ausgaben/<int:pk>/bearbeiten/", views.ExpenseUpdateView.as_view(), name="expense_update"),
    path("ausgaben/<int:pk>/loeschen/", views.ExpenseArchiveView.as_view(), name="expense_archive"),
    path("ust-berichte/neu/", views.TaxReportCreateView.as_view(), name="tax_report_create"),
    path("ust-berichte/<int:pk>/bearbeiten/", views.TaxReportUpdateView.as_view(), name="tax_report_update"),
    path("ust-berichte/<int:pk>/loeschen/", views.TaxReportDeleteView.as_view(), name="tax_report_delete"),
]
