from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "due_date", "is_done", "assigned_to", "related_order"]
    list_filter = ["is_done", "tags"]
    search_fields = ["title", "description"]
