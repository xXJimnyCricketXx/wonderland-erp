from core.models import ReferenceOption

from .colors import annotate_colors, build_color_map
from .models import Appointment


def pending_reminders(request):
    """Powers the navbar bell icon on every page - not just inside the
    Termine app - so it has to be a context processor rather than living in
    a single view. is_reminder_due is pure datetime math (no extra query
    per appointment), so filtering candidates in Python is fine at this
    scale."""
    if not request.user.is_authenticated:
        return {}

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

    return {
        "pending_reminders": due,
        "pending_reminder_count": len(due),
    }
