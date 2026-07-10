from django.db import models

from catalog.models import Article
from contacts.models import Customer
from core.models import Archivable
from knowledge.models import PackagingType


class Order(Archivable):
    order_id = models.CharField("Bestell-ID", max_length=50, unique=True)
    customer = models.ForeignKey(
        Customer, verbose_name="Kunde", on_delete=models.PROTECT, related_name="orders"
    )

    sale_date = models.DateField("Verkaufsdatum")
    date_shipped = models.DateField("Versendet am", blank=True, null=True)

    shipping_carrier = models.CharField("Versandunternehmen", max_length=100, blank=True)
    tracking_number = models.CharField("Sendungsnummer", max_length=100, blank=True)
    # FK to the LUCID packaging-weight lookup, so yearly Verpackungsregister
    # totals can be computed from actual order volume instead of hand-counted.
    package_type = models.ForeignKey(
        PackagingType, verbose_name="Versendet als", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="orders",
    )

    number_of_items = models.PositiveIntegerField("Anzahl Artikel", default=1)
    payment_method = models.CharField("Zahlungsmethode", max_length=100, blank=True)
    payment_type = models.CharField("Zahlungsart", max_length=100, blank=True)
    order_type = models.CharField("Bestellart", max_length=100, blank=True)
    status = models.CharField("Status", max_length=100, blank=True)

    # Etsy's own username for the buyer - distinct from Customer.full_name,
    # which is the real/shipping name.
    buyer_username = models.CharField("Etsy-Benutzername", max_length=255, blank=True)

    # Delivery address as of the order date - deliberately separate from
    # Customer's (billing) address so past orders stay historically correct
    # even if the customer later moves.
    ship_street1 = models.CharField("Straße & Hausnummer", max_length=255, blank=True)
    ship_street2 = models.CharField("Adresszusatz", max_length=255, blank=True)
    ship_city = models.CharField("Ort", max_length=255, blank=True)
    ship_state = models.CharField("Bundesland/Region", max_length=255, blank=True)
    ship_zipcode = models.CharField("PLZ", max_length=20, blank=True)
    ship_country = models.CharField("Land", max_length=100, blank=True)

    currency = models.CharField("Währung", max_length=3, default="EUR")
    order_value = models.DecimalField("Bestellwert", max_digits=10, decimal_places=2, default=0)
    coupon_code = models.CharField("Gutscheincode", max_length=100, blank=True)
    coupon_details = models.CharField("Gutschein-Details", max_length=255, blank=True)
    discount_amount = models.DecimalField("Rabattbetrag", max_digits=10, decimal_places=2, default=0)
    shipping_discount = models.DecimalField(
        "Versandrabatt", max_digits=10, decimal_places=2, default=0
    )
    shipping = models.DecimalField("Versandkosten", max_digits=10, decimal_places=2, default=0)
    sales_tax = models.DecimalField("Umsatzsteuer", max_digits=10, decimal_places=2, default=0)
    order_total = models.DecimalField("Bestellsumme", max_digits=10, decimal_places=2, default=0)
    card_processing_fees = models.DecimalField(
        "Kartengebühren", max_digits=10, decimal_places=2, default=0
    )
    order_net = models.DecimalField("Netto-Bestellwert", max_digits=10, decimal_places=2, default=0)
    adjusted_order_total = models.DecimalField(
        "Korrigierte Bestellsumme", max_digits=10, decimal_places=2, blank=True, null=True
    )
    adjusted_card_processing_fees = models.DecimalField(
        "Korrigierte Kartengebühren", max_digits=10, decimal_places=2, blank=True, null=True
    )
    adjusted_net_order_amount = models.DecimalField(
        "Korrigierter Netto-Bestellwert", max_digits=10, decimal_places=2, blank=True, null=True
    )

    inperson_discount = models.DecimalField(
        "Vor-Ort-Rabatt", max_digits=10, decimal_places=2, blank=True, null=True
    )
    inperson_location = models.CharField("Vor-Ort-Standort", max_length=255, blank=True)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"
        ordering = ["-sale_date"]

    def __str__(self):
        return f"Bestellung #{self.order_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, verbose_name="Bestellung", on_delete=models.CASCADE, related_name="items"
    )
    article = models.ForeignKey(
        Article, verbose_name="Artikel", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="order_items",
    )

    # Etsy's SKU export is unreliable (supplier codes, plain numbers, blanks -
    # see docs/konzept.md), so the raw value is always kept even when article
    # matching fails or is ambiguous.
    sku_raw = models.CharField("SKU (roh)", max_length=255, blank=True)
    position = models.PositiveIntegerField("Position", default=1)

    class Meta:
        verbose_name = "Bestellposition"
        verbose_name_plural = "Bestellpositionen"
        ordering = ["order", "position"]

    def __str__(self):
        return f"{self.order} - {self.sku_raw or self.article}"


class Review(models.Model):
    order = models.ForeignKey(
        Order, verbose_name="Bestellung", on_delete=models.CASCADE, related_name="reviews"
    )

    reviewer_name = models.CharField("Rezensent", max_length=255)
    date_reviewed = models.DateField("Bewertungsdatum")
    star_rating = models.PositiveSmallIntegerField("Sternebewertung")
    message = models.TextField("Text", blank=True)

    class Meta:
        verbose_name = "Bewertung"
        verbose_name_plural = "Bewertungen"
        ordering = ["-date_reviewed"]

    def __str__(self):
        return f"{self.reviewer_name} - {self.star_rating}★"
