"""Shared shape for the navbar notification bell/modal - each app that wants
to surface something there (Termine reminders, Artikel stock warnings,
Kontakte birthdays/overdue follow-up, Aufgaben due dates, ...) contributes a
get_*_notifications(request) function that returns a list of Notification
objects; core.context_processors.notifications combines them into one feed
instead of every source needing its own bell."""

from dataclasses import dataclass

# Same pastel palette already used for appointment-type colors, reused here
# as fixed severity colors so Artikel-Lagerwarnungen read as genuinely
# "warning"/"danger" rather than an arbitrary category color.
LEVEL_COLORS = {
    "danger": ("#FDD8DE", "#790619"),
    "warning": ("#FFF3C4", "#7A5B00"),
    "info": ("#CFE0FC", "#0A47A9"),
    "success": ("#C7F5D9", "#0B4121"),
}


def color_for_level(level):
    return LEVEL_COLORS.get(level, LEVEL_COLORS["info"])


@dataclass
class Notification:
    header: str
    subtitle: str
    body: str
    bg_color: str
    fg_color: str
    detail_url: str = ""
    dismiss_url: str = ""


def get_all_notifications(request):
    from appointments.notifications import get_reminder_notifications
    from catalog.notifications import get_stock_notifications
    from contacts.notifications import get_contact_notifications
    from tasks.notifications import get_task_notifications

    return (
        get_reminder_notifications(request)
        + get_stock_notifications(request)
        + get_contact_notifications(request)
        + get_task_notifications(request)
    )
