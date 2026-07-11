from django.urls import reverse

from core.models import ReferenceOption
from core.notifications import Notification

from .colors import annotate_colors, build_color_map
from .models import Appointment


def get_reminder_notifications(request):
    if not request.user.is_authenticated:
        return []

    candidates = Appointment.objects.filter(
        has_reminder=True, reminder_dismissed=False
    ).select_related("supplier").prefetch_related("customers")

    due = [appt for appt in candidates if appt.is_reminder_due]
    due.sort(key=lambda a: a.reminder_trigger_at)

    color_map = build_color_map(
        ReferenceOption.objects.filter(category="appointment_type")
        .order_by("order", "value").values_list("value", flat=True)
    )
    annotate_colors(due, color_map)

    notifications = []
    for appt in due:
        time_str = f" {appt.start_time:%H:%M}" if appt.start_time else ""
        body = f"{appt.start_time:%H:%M} – {appt.title}" if appt.start_time else appt.title
        notifications.append(Notification(
            header="Terminerinnerung",
            subtitle=f"{appt.start_date:%d.%m.%Y}{time_str}",
            body=body,
            bg_color=appt.bg_color,
            fg_color=appt.fg_color,
            detail_url="",
            dismiss_url=reverse("appointments:reminder_dismiss", args=[appt.pk]),
        ))
    return notifications
