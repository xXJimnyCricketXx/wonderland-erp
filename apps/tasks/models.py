from django.conf import settings
from django.db import models

from core.models import ReferenceOption
from orders.models import Order


class Task(models.Model):
    title = models.CharField("Titel", max_length=255)
    description = models.TextField("Beschreibung", blank=True)
    due_date = models.DateField("Fällig am", blank=True, null=True)
    is_done = models.BooleanField("Erledigt", default=False)

    tags = models.ManyToManyField(
        ReferenceOption,
        verbose_name="Tags",
        blank=True,
        related_name="tasks",
        limit_choices_to={"category": "task_tag"},
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Zugewiesen an", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks_assigned",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Erstellt von", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Bearbeitet von", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks_updated",
    )

    related_order = models.ForeignKey(
        Order, verbose_name="Bestellung", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks",
    )

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Aufgabe"
        verbose_name_plural = "Aufgaben"
        ordering = ["is_done", "due_date"]

    def __str__(self):
        return self.title
