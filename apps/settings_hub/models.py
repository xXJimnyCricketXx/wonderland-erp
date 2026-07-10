from django.db import models


class CompanyProfile(models.Model):
    """Singleton - our own company master data (Stammdaten). Always pk=1,
    see CompanyProfile.load()."""

    company_name = models.CharField("Firmenname", max_length=255, blank=True)

    street1 = models.CharField("Straße & Hausnummer", max_length=255, blank=True)
    street2 = models.CharField("Adresszusatz", max_length=255, blank=True)
    zipcode = models.CharField("PLZ", max_length=20, blank=True)
    city = models.CharField("Ort", max_length=255, blank=True)
    country = models.CharField("Land", max_length=100, blank=True)

    tax_number = models.CharField("Steuernummer", max_length=50, blank=True)
    vat_id = models.CharField("USt-ID", max_length=50, blank=True)

    email = models.EmailField("E-Mail", blank=True)
    website = models.URLField("Website", blank=True)

    etsy_shop_url = models.URLField("Etsy-Shop", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)

    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Firmenprofil"
        verbose_name_plural = "Firmenprofil"

    def __str__(self):
        return self.company_name or "Firmenprofil"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class BackupSettings(models.Model):
    """Singleton - see CompanyProfile.load() for the pattern. Not touched by
    a database reset, since retention count is config, not business data."""

    keep_count = models.PositiveIntegerField("Anzahl aufzubewahrender Backups", default=3)

    class Meta:
        verbose_name = "Backup-Einstellungen"
        verbose_name_plural = "Backup-Einstellungen"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
