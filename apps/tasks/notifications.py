from datetime import date

from django.urls import reverse

from core.notifications import Notification, color_for_level

from .models import Task


def get_task_notifications(request):
    if not request.user.is_authenticated:
        return []

    overdue = Task.objects.filter(
        is_archived=False, due_date__lt=date.today()
    ).exclude(status="done").order_by("due_date")

    bg, fg = color_for_level("danger")
    notifications = []
    for task in overdue:
        notifications.append(Notification(
            header="Aufgabe überfällig",
            subtitle=f"Fällig: {task.due_date:%d.%m.%Y}",
            body=task.title,
            bg_color=bg,
            fg_color=fg,
            detail_url=reverse("tasks:board"),
            dismiss_url="",
        ))
    return notifications
