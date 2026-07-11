from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.CalendarView.as_view(), name="calendar"),
    path("neu/", views.AppointmentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.AppointmentUpdateView.as_view(), name="update"),
    path("<int:pk>/loeschen/", views.AppointmentDeleteView.as_view(), name="delete"),
    path("<int:pk>/erinnerung-verwerfen/", views.ReminderDismissView.as_view(), name="reminder_dismiss"),
]
