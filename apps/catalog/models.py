from django.db import models

from contacts.models import Supplier
from core.models import Archivable


class Article(Archivable):
    # Our own "dumb" identifier going forward (e.g. WD-0001) - Etsy's own
    # BESTANDSEINHEIT field is unreliable historically, see docs/konzept.md.
    sku = models.CharField("SKU", max_length=50, unique=True, blank=True, null=True)
    title = models.CharField("Titel", max_length=255)
    description = models.TextField("Beschreibung", blank=True)

    # Free text, options managed via ReferenceOption(category="article_category")
    # - not delivered by the Etsy listings CSV, maintained manually.
    category = models.CharField("Kategorie", max_length=100, blank=True)

    price = models.DecimalField("Preis", max_digits=10, decimal_places=2)
    currency_code = models.CharField("Währung", max_length=3, default="EUR")

    stock_quantity = models.PositiveIntegerField("Lagerbestand", default=0)
    # Reorder threshold ("Soll-Lagerbestand") - see needs_restock below for
    # how this and stock_quantity combine into a low-stock warning.
    minimum_stock_quantity = models.PositiveIntegerField("Soll-Lagerbestand", blank=True, null=True)

    supplier = models.ForeignKey(
        Supplier, verbose_name="Lieferant", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="articles",
    )
    is_active = models.BooleanField("Aktiv gelistet", default=True)

    thumbnail_url = models.URLField("Vorschaubild-URL", blank=True)
    shop_url = models.URLField("Shop-Link", blank=True)

    # Grundpreis - market rate for the raw material, e.g. 0.10 EUR/g.
    purchase_price_per_unit = models.DecimalField(
        "Grundpreis", max_digits=10, decimal_places=4, blank=True, null=True
    )
    purchase_price_unit_label = models.CharField("Grundpreis-Einheit", max_length=20, blank=True)
    # What one finished piece cost, e.g. 2.50 EUR for one Trommelstein - a
    # "gesamt" total is deliberately NOT a stored field, since it's ambiguous
    # whether that should mean current stock or target stock; instead it's
    # computed and clearly labeled from this figure (see the properties below).
    purchase_price_per_piece = models.DecimalField(
        "Einkaufspreis pro Stück", max_digits=10, decimal_places=2, blank=True, null=True
    )

    # A variant (e.g. "Ausführung: A") is a full Article in its own right -
    # own SKU/stock/price/image - linked back to the listing it belongs to
    # rather than living in a separate variant table.
    parent_article = models.ForeignKey(
        "self", verbose_name="Hauptartikel", on_delete=models.CASCADE,
        null=True, blank=True, related_name="variants",
    )
    variant_label = models.CharField("Variante", max_length=100, blank=True)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} ({self.variant_label})" if self.variant_label else self.title

    def _is_low_stock(self):
        if self.minimum_stock_quantity is None:
            return self.stock_quantity == 0
        return self.stock_quantity <= self.minimum_stock_quantity

    @property
    def purchase_value_current_stock(self):
        """Einkaufswert für den aktuellen Lagerbestand (Stückpreis × Bestand)."""
        if self.purchase_price_per_piece is None:
            return None
        return self.purchase_price_per_piece * self.stock_quantity

    @property
    def purchase_value_target_stock(self):
        """Einkaufswert, um den Soll-Lagerbestand zu erreichen (Stückpreis × Soll-Bestand)."""
        if self.purchase_price_per_piece is None or self.minimum_stock_quantity is None:
            return None
        return self.purchase_price_per_piece * self.minimum_stock_quantity

    @property
    def needs_restock(self):
        """True if this article or any of its variants is low on stock -
        so a parent can show a single warning covering all its variants."""
        if self._is_low_stock():
            return True
        return any(variant._is_low_stock() for variant in self.variants.all())
