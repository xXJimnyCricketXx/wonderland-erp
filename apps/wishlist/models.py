from django.db import models

from core.models import ReferenceOption


class WishlistItem(models.Model):
    title = models.CharField("Titel", max_length=255)
    notes = models.TextField("Notizen", blank=True)

    # Link to the shop/listing this was spotted in, if it's a concrete offer
    # rather than pure inspiration.
    source_url = models.URLField("Link zum Angebot", blank=True)
    estimated_price = models.DecimalField(
        "Geschätzter Preis", max_digits=10, decimal_places=2, blank=True, null=True
    )

    # Free text, options managed via ReferenceOption(category="wishlist_status").
    status = models.CharField("Status", max_length=50, blank=True, default="Idee")

    # Controlled vocabulary via the shared reference-data table, rather than a
    # dedicated Tag model - prevents duplicate tags from inconsistent spelling.
    tags = models.ManyToManyField(
        ReferenceOption,
        verbose_name="Tags",
        blank=True,
        related_name="wishlist_items",
        limit_choices_to={"category": "wishlist_tag"},
    )

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Inspirationboard-Eintrag"
        verbose_name_plural = "Inspirationboard-Einträge"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class WishlistItemImage(models.Model):
    # Up to 5 per item - enforced in the form/view layer, not the database.
    item = models.ForeignKey(
        WishlistItem, verbose_name="Eintrag", on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField("Bild (Upload)", upload_to="wishlist/", blank=True, null=True)
    image_url = models.URLField("Bild-Link", blank=True)
    position = models.PositiveIntegerField("Reihenfolge", default=1)

    class Meta:
        verbose_name = "Inspirationboard-Bild"
        verbose_name_plural = "Inspirationboard-Bilder"
        ordering = ["item", "position"]

    def __str__(self):
        return f"{self.item} - Bild {self.position}"
