from django.db import models

from core.models import Archivable


class ShoppingListItem(Archivable):
    """Freie Merkliste fuer Artikel, die (nach)gekauft werden sollen - z.B.
    weil ein eigener Artikel ausverkauft ist oder man bei einem Haendler
    etwas Interessantes gesehen hat. Bewusst kein Pflichtfeld ausser
    Anzahl: nicht jeder Haendler vergibt Artikelnummern (z.B. Vor-Ort-Kauf
    ohne Katalog), daher muessen Artikel-Nr./Titel/Preis/etc. frei bleiben
    duerfen."""

    article_number = models.CharField("Artikel-Nr.", max_length=100, blank=True)
    title = models.CharField("Artikel", max_length=255, blank=True)
    quantity = models.PositiveIntegerField("Anzahl", default=1)
    price_each = models.DecimalField("Preis (einzeln)", max_digits=10, decimal_places=2, blank=True, null=True)
    # Nicht aus quantity*price_each abgeleitet, sondern ein eigenes Feld -
    # wird im Formular per JS automatisch vorausgefuellt, bleibt aber
    # ueberschreibbar (z.B. bei Mengenrabatt, der nicht linear ist).
    price_total = models.DecimalField("Preis (gesamt)", max_digits=10, decimal_places=2, blank=True, null=True)
    # Dropdown auf den Lieferanten-Stamm statt Freitext, damit Schreibweisen
    # konsistent bleiben - optional, da man auch vor Ort bei einem noch nicht
    # erfassten Haendler etwas sehen kann.
    supplier = models.ForeignKey(
        "contacts.Supplier", verbose_name="Händler", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="shopping_list_items",
    )
    shop_url = models.URLField("Shopseite", blank=True)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Einkaufslisten-Eintrag"
        verbose_name_plural = "Einkaufsliste"
        ordering = ["supplier__last_name", "supplier__first_name", "title"]

    def __str__(self):
        return self.title or self.article_number or f"Einkaufslisten-Eintrag #{self.pk}"


class ShoppingListItemImage(models.Model):
    # Bis zu 5 pro Eintrag (im Formular begrenzt, wie beim Inspirationboard) -
    # das erste (niedrigste position) ist das Vorschaubild in der Tabelle.
    # Reiner Link, kein Upload - ein Download+Reupload fuer jedes
    # Produktbild waere unnoetiger Aufwand.
    item = models.ForeignKey(
        ShoppingListItem, verbose_name="Eintrag", on_delete=models.CASCADE, related_name="images"
    )
    image_url = models.URLField("Bild-Link")
    position = models.PositiveIntegerField("Reihenfolge", default=1)

    class Meta:
        verbose_name = "Einkaufslisten-Bild"
        verbose_name_plural = "Einkaufsliste-Bilder"
        ordering = ["item", "position"]

    def __str__(self):
        return f"{self.item} - Bild {self.position}"
