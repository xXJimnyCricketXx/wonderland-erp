from django.db import models


class KnowledgeEntry(models.Model):
    title = models.CharField("Titel", max_length=255)
    content = models.TextField("Inhalt", blank=True)
    featured_image = models.ImageField("Beitragsbild", upload_to="knowledge/", blank=True, null=True)
    tags = models.CharField("Tags", max_length=255, blank=True)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Infothek-Eintrag"
        verbose_name_plural = "Infothek-Einträge"
        ordering = ["title"]

    def __str__(self):
        return self.title


class PackagingType(models.Model):
    """LUCID/Verpackungsregister reference data - per-shipment material
    weights, e.g. "Luftpolstertasche S" -> 0.015kg paper/unit. Yearly totals
    are computed from Order.package_type usage, not stored here."""

    name = models.CharField("Bezeichnung", max_length=100, unique=True)
    paper_kg_per_unit = models.DecimalField(
        "Papier/Pappe/Karton (kg pro Stück)", max_digits=6, decimal_places=4, default=0
    )
    plastic_kg_per_unit = models.DecimalField(
        "Kunststoffe (kg pro Stück)", max_digits=6, decimal_places=4, default=0
    )
    glass_kg_per_unit = models.DecimalField(
        "Glas (kg pro Stück)", max_digits=6, decimal_places=4, default=0
    )
    valid_from = models.DateField("Gültig ab", blank=True, null=True)

    class Meta:
        verbose_name = "Verpackungsart"
        verbose_name_plural = "Verpackungsarten"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ShippingOption(models.Model):
    carrier = models.CharField("Anbieter", max_length=100)
    description = models.CharField("Beschreibung", max_length=255)
    use_case = models.CharField("Anwendung", max_length=255, blank=True)
    # Kept as text - not always a clean number (e.g. "X (+4,00)" for a
    # tracking surcharge on top of a base rate).
    price_note = models.CharField("Preis", max_length=100, blank=True)
    payment_method = models.CharField("Bezahlen", max_length=50, blank=True)
    requires_tracking_number = models.BooleanField("Sendungsnummer nötig", default=False)
    is_international = models.BooleanField("International", default=False)
    valid_from = models.DateField("Gültig ab", blank=True, null=True)

    class Meta:
        verbose_name = "Versandoption"
        verbose_name_plural = "Versandoptionen"
        ordering = ["carrier", "description"]

    def __str__(self):
        return f"{self.carrier} - {self.description}"


class CustomsTariffCode(models.Model):
    code = models.CharField("Zolltarifnummer", max_length=20, unique=True)
    definition = models.CharField("Definition", max_length=255)
    description = models.CharField("Beschreibung", max_length=255, blank=True)

    class Meta:
        verbose_name = "Zolltarifnummer"
        verbose_name_plural = "Zolltarifnummern"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.definition}"
