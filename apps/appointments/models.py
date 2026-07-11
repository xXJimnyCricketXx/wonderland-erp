from datetime import datetime, time

from django.db import models
from django.utils import timezone

from contacts.models import Customer, Supplier

REMINDER_LEAD_CHOICES = [
    (5, "5 Minuten vorher"),
    (15, "15 Minuten vorher"),
    (30, "30 Minuten vorher"),
    (60, "1 Stunde vorher"),
    (120, "2 Stunden vorher"),
    (1440, "1 Tag vorher"),
]


class Appointment(models.Model):
    title = models.CharField("Titel", max_length=255)

    start_date = models.DateField("Startdatum")
    end_date = models.DateField("Enddatum")
    is_all_day = models.BooleanField("Ganztägig", default=True)
    start_time = models.TimeField("Startzeit", blank=True, null=True)
    end_time = models.TimeField("Endzeit", blank=True, null=True)

    # Free text, options managed via ReferenceOption(category="appointment_type")
    # in the Referenzdaten settings screen - also drives the color shown in
    # the calendar (see appointments.colors).
    event_type = models.CharField("Termin-Typ", max_length=50, blank=True)

    # A single appointment (e.g. a market stall, a group consultation) can
    # involve several customers at once - unlike Order.customer, which is
    # always exactly one buyer.
    customers = models.ManyToManyField(
        Customer, verbose_name="Kunden", blank=True, related_name="appointments",
    )
    supplier = models.ForeignKey(
        Supplier, verbose_name="Lieferant", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="appointments",
    )

    location = models.CharField("Ort", max_length=255, blank=True)
    description = models.TextField("Beschreibung", blank=True)

    has_reminder = models.BooleanField("Erinnerung", default=False)
    reminder_lead_minutes = models.PositiveIntegerField(
        "Vorlaufzeit", choices=REMINDER_LEAD_CHOICES, blank=True, null=True, default=30,
    )
    # Set once the user has acknowledged the reminder in the navbar bell -
    # these are one-off appointments (no recurrence), so a permanent
    # dismissal is enough; it doesn't need to reset for a next occurrence.
    reminder_dismissed = models.BooleanField("Erinnerung verworfen", default=False)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Termin"
        verbose_name_plural = "Termine"
        ordering = ["start_date", "start_time"]

    def __str__(self):
        return f"{self.title} ({self.start_date:%d.%m.%Y})"

    @property
    def reminder_trigger_at(self):
        if not self.has_reminder or not self.reminder_lead_minutes:
            return None
        naive = datetime.combine(self.start_date, self.start_time or time(0, 0))
        aware = timezone.make_aware(naive) if timezone.is_naive(naive) else naive
        return aware - timezone.timedelta(minutes=self.reminder_lead_minutes)

    @property
    def is_reminder_due(self):
        trigger = self.reminder_trigger_at
        return bool(trigger and not self.reminder_dismissed and trigger <= timezone.now())
