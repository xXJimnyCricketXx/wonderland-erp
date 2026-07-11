from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "due_date", "status", "assigned_to", "related_order", "is_archived"]
    list_filter = ["status", "tags", "is_archived"]
    search_fields = ["title", "description"]
