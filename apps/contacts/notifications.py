from datetime import date

from django.urls import reverse

from core.notifications import Notification, color_for_level

from .models import Customer, Supplier


def _birthday_notifications():
    today = date.today()
    bg, fg = color_for_level("success")
    notifications = []
    for customer in Customer.objects.filter(
        is_archived=False, birthday__month=today.month, birthday__day=today.day,
    ):
        notifications.append(Notification(
            header="Geburtstag",
            subtitle=today.strftime("%d.%m."),
            body=f"{customer.full_name} hat heute Geburtstag",
            bg_color=bg,
            fg_color=fg,
            detail_url=f"{reverse('contacts:list')}?tab=kunden&q={customer.last_name}",
            dismiss_url="",
        ))
    return notifications


def _needs_attention_notifications():
    # ContactQuerySet.needs_attention() excludes contacts with no
    # last_contact_at at all (last_contact_at__lt=cutoff drops NULLs in
    # SQL) - someone never contacted doesn't get flagged here, only ones
    # that went quiet after an actual last contact.
    bg, fg = color_for_level("info")
    notifications = []
    sources = [(Customer, "kunden", "Kunde"), (Supplier, "lieferanten", "Lieferant")]
    for model, tab, label in sources:
        for contact in model.objects.filter(is_archived=False).needs_attention(days=30):
            notifications.append(Notification(
                header="Kontakt überfällig",
                subtitle=label,
                body=f"{contact.full_name} – letzter Kontakt: {contact.last_contact_at:%d.%m.%Y}",
                bg_color=bg,
                fg_color=fg,
                detail_url=f"{reverse('contacts:list')}?tab={tab}&q={contact.last_name}",
                dismiss_url="",
            ))
    return notifications


def get_contact_notifications(request):
    if not request.user.is_authenticated:
        return []
    return _birthday_notifications() + _needs_attention_notifications()
