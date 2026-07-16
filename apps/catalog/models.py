from django.db import models

from contacts.models import Supplier
from core.models import Archivable


def next_wd_sku():
    """Naechste freie fortlaufende WD-XXXX-Nummer - selbe Logik wie das
    assign_skus-Management-Command, hier aber fuer einen einzelnen neuen
    Artikel statt fuer einen einmaligen Bulk-Nachtrag."""
    existing_numbers = [
        int(sku[3:7])
        for sku in Article.objects.exclude(sku__isnull=True).exclude(sku="").values_list("sku", flat=True)
        if sku.startswith("WD-") and sku[3:7].isdigit()
    ]
    next_number = max(existing_numbers, default=0) + 1
    return f"WD-{next_number:04d}"


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
    # Target stock level to hold ("Soll-Lagerbestand"), not a reorder
    # threshold - see needs_restock below for how this and stock_quantity
    # combine into a low-stock warning.
    minimum_stock_quantity = models.PositiveIntegerField("Soll-Lagerbestand", blank=True, null=True)

    supplier = models.ForeignKey(
        Supplier, verbose_name="Lieferant", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="articles",
    )
    is_active = models.BooleanField("Aktiv gelistet", default=True)
    # Unabhaengig von is_active: "Aktiv gelistet"=Nein heisst bewusst vom
    # Shop genommen (z.B. Bernstein aus rechtlichen Gruenden), "Ausverkauft"
    # heisst schlicht kein Nachschub geplant (z.B. Einzelstueck) - beides
    # kann unabhaengig voneinander zutreffen.
    is_sold_out = models.BooleanField("Ausverkauft", default=False)

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
        # No warning without an explicit Soll-Bestand - stock=0 alone isn't
        # enough, since e.g. freshly imported variants sit at 0 until their
        # real stock is entered manually (Etsy's listing export doesn't give
        # per-variant counts). Soll-Bestand is the target level to hold, not
        # a reorder threshold - being exactly at it is fine, only falling
        # below it warrants a warning.
        if self.minimum_stock_quantity is None:
            return False
        return self.stock_quantity < self.minimum_stock_quantity

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


class EtsyListingMapping(models.Model):
    """One-time mapping "this Etsy listing + variation = this Article", keyed
    by Etsy's stable Listing ID (from the Sold-Order-Items export - see
    data_import.order_item_import) PLUS the raw Etsy variation text
    ("Sorte: Amazonit"). A single listing can bundle several genuinely
    different products under "Different varieties" - keying on listing_id
    alone would force every variation onto the same Article. Set this once
    per (listing, variation) and every matching past/future OrderItem picks
    up the article automatically, instead of assigning it order by order."""

    listing_id = models.CharField("Etsy-Listing-ID", max_length=50)
    # Freitext wie in OrderItem.variations ("Sorte: Amazonit") - leer, wenn
    # das Listing gar keine Variationen hat (dann greift diese eine Zeile
    # fuer alle Bestellpositionen dieses Listings).
    variations = models.CharField("Variante", max_length=255, blank=True)
    # Cached from the last-seen order item, purely for display context when
    # picking the article (Etsy's item name, not necessarily = Article.title).
    item_name = models.CharField("Etsy-Artikelname", max_length=255, blank=True)
    article = models.ForeignKey(
        Article, verbose_name="Artikel", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="listing_mappings",
    )

    class Meta:
        verbose_name = "Etsy-Listing-Zuordnung"
        verbose_name_plural = "Etsy-Listing-Zuordnungen"
        ordering = ["item_name", "variations"]
        unique_together = [("listing_id", "variations")]

    def __str__(self):
        label = f"{self.item_name} ({self.listing_id})"
        return f"{label} - {self.variations}" if self.variations else label
