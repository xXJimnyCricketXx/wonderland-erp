from django.db import models

from core.models import Archivable


class ShoppingListItem(Archivable):
    """Freie Merkliste fuer Artikel, die (nach)gekauft werden sollen - z.B.
    weil ein eigener Artikel ausverkauft ist oder man bei einem Haendler
    etwas Interessantes gesehen hat. Bewusst kein Pflichtfeld ausser
    Anzahl: nicht jeder Haendler vergibt Artikelnummern (z.B. Vor-Ort-Kauf
    ohne Katalog), daher muessen Artikel-Nr./Titel/Preis/etc. frei bleiben
    duerfen. Bild ist ein reiner Link (kein Upload) - ein Download+Reupload
    fuer jedes Produktbild waere unnoetiger Aufwand."""

    article_number = models.CharField("Artikel-Nr.", max_length=100, blank=True)
    title = models.CharField("Artikel", max_length=255, blank=True)
    quantity = models.PositiveIntegerField("Anzahl", default=1)
    price_each = models.DecimalField("Preis (einzeln)", max_digits=10, decimal_places=2, blank=True, null=True)
    # Nicht aus quantity*price_each abgeleitet, sondern ein eigenes Feld -
    # wird im Formular per JS automatisch vorausgefuellt, bleibt aber
    # ueberschreibbar (z.B. bei Mengenrabatt, der nicht linear ist).
    price_total = models.DecimalField("Preis (gesamt)", max_digits=10, decimal_places=2, blank=True, null=True)
    image_url = models.URLField("Bild (Link)", blank=True)
    supplier_name = models.CharField("Händler", max_length=255, blank=True)
    shop_url = models.URLField("Shopseite", blank=True)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Einkaufslisten-Eintrag"
        verbose_name_plural = "Einkaufsliste"
        ordering = ["supplier_name", "title"]

    def __str__(self):
        return self.title or self.article_number or f"Einkaufslisten-Eintrag #{self.pk}"
