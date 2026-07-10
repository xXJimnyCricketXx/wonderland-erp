from django.db import models
from django.utils import timezone


class ArchivableQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_archived=False)

    def archived(self):
        return self.filter(is_archived=True)


class Archivable(models.Model):
    """ERP convention: records get archived, not deleted, so historical data
    (past orders, discontinued articles, old contacts) never just vanishes."""

    is_archived = models.BooleanField("Archiviert", default=False)
    archived_at = models.DateTimeField("Archiviert am", blank=True, null=True)

    objects = ArchivableQuerySet.as_manager()

    class Meta:
        abstract = True

    def archive(self):
        self.is_archived = True
        self.archived_at = timezone.now()
        self.save(update_fields=["is_archived", "archived_at"])

    def unarchive(self):
        self.is_archived = False
        self.archived_at = None
        self.save(update_fields=["is_archived", "archived_at"])


class ReferenceOption(models.Model):
    """Generic, user-extensible option list (status values, payment types,
    VAT rates, ...) - lives in a settings/'Referenzdaten' screen later rather
    than as hardcoded choices=, so adding an option needs no code change."""

    category = models.CharField("Kategorie", max_length=100)
    value = models.CharField("Wert", max_length=255)
    order = models.PositiveIntegerField("Reihenfolge", default=0)

    class Meta:
        verbose_name = "Referenzwert"
        verbose_name_plural = "Referenzwerte"
        unique_together = [("category", "value")]
        ordering = ["category", "order", "value"]

    def __str__(self):
        return f"{self.category}: {self.value}"
