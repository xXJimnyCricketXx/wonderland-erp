from datetime import date, timedelta

from django.urls import reverse

from core.notifications import Notification, color_for_level

from .models import PackagingLicenseSubmission

# Reminder window - starts nagging this many days before the due date, stays
# up (as a "danger" once overdue) until marked submitted.
REMINDER_LEAD_DAYS = 30


def get_license_submission_notifications(request):
    if not request.user.is_authenticated:
        return []

    today = date.today()
    candidates = [
        (today.year - 1, PackagingLicenseSubmission.TYPE_JAHRESABSCHLUSSMELDUNG),
        (today.year, PackagingLicenseSubmission.TYPE_PLANMENGENANPASSUNG),
        (today.year - 1, PackagingLicenseSubmission.TYPE_LUCID_MELDUNG),
    ]

    notifications = []
    for year, submission_type in candidates:
        submission, _ = PackagingLicenseSubmission.objects.get_or_create(
            year=year, submission_type=submission_type
        )
        if submission.submitted:
            continue
        if today < submission.due_date - timedelta(days=REMINDER_LEAD_DAYS):
            continue

        overdue = today > submission.due_date
        bg, fg = color_for_level("danger" if overdue else "warning")
        notifications.append(Notification(
            header=submission.get_submission_type_display(),
            subtitle=f"Fällig: {submission.due_date:%d.%m.%Y}",
            body=(
                f"{submission.get_submission_type_display()} für {year} ist "
                f"{'überfällig' if overdue else 'bald fällig'} und noch nicht als abgegeben markiert."
            ),
            bg_color=bg,
            fg_color=fg,
            detail_url=reverse("knowledge:infothek") + "?tab=verpackungslizenz",
            dismiss_url=reverse("knowledge:license_submission_confirm", args=[submission.pk]),
        ))
    return notifications
