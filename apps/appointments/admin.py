from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["title", "start_date", "end_date", "event_type", "supplier", "has_reminder"]
    list_filter = ["event_type", "is_all_day", "has_reminder"]
    search_fields = ["title", "location", "description"]
    filter_horizontal = ["customers"]
