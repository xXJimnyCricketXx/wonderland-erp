from django.urls import path

from . import views

app_name = "astro"

urlpatterns = [
    path("neu/", views.BirthChartCreateView.as_view(), name="birth_chart_create"),
    path("ort-vorschlaege/", views.BirthChartGeocodeSuggestView.as_view(), name="birth_chart_geocode_suggest"),
    path("<int:pk>/", views.BirthChartDetailModalView.as_view(), name="birth_chart_detail"),
    path("<int:pk>/bearbeiten/", views.BirthChartUpdateView.as_view(), name="birth_chart_update"),
    path("<int:pk>/loeschen/", views.BirthChartDeleteView.as_view(), name="birth_chart_delete"),
    path("<int:pk>/bericht/", views.BirthChartReportView.as_view(), name="birth_chart_report"),
]
