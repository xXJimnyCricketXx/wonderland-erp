from decimal import Decimal

from django.db import models

from contacts.models import Supplier
from core.models import Archivable
from orders.models import Order


class SKR03Account(models.Model):
    number = models.CharField("Kontonummer", max_length=10, unique=True)
    name = models.CharField("Bezeichnung", max_length=255)

    class Meta:
        verbose_name = "SKR03-Konto"
        verbose_name_plural = "SKR03-Konten"
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.name}"


class AccountMapping(models.Model):
    """Maps a category ('Art', e.g. Expense.category or LedgerEntry.entry_type)
    plus an optional sub-classification ('Variante') to an SKR03 account -
    e.g. 'Versand/Porto' + 'Porto DP AG' -> 4910 Porto (ohne USt)."""

    art = models.CharField("Art", max_length=100)
    variante = models.CharField("Variante", max_length=100, blank=True)
    skr03_account = models.ForeignKey(
        SKR03Account, verbose_name="SKR03-Konto", on_delete=models.SET_NULL, null=True
    )

    class Meta:
        verbose_name = "Konten-Zuordnung"
        verbose_name_plural = "Konten-Zuordnungen"
        unique_together = [("art", "variante")]
        ordering = ["art", "variante"]

    def __str__(self):
        label = f"{self.art} ({self.variante})" if self.variante else self.art
        return f"{label} -> {self.skr03_account}"

    @classmethod
    def account_for(cls, art, variante=""):
        mapping = cls.objects.filter(art=art, variante=variante).first()
        return mapping.skr03_account if mapping else None


class Expense(Archivable):
    date = models.DateField("Datum")

    # Free text, options managed via ReferenceOption(category="expense_category")
    # - matches AccountMapping.art for the SKR03 lookup.
    category = models.CharField("Kategorie", max_length=100)
    variant = models.CharField("Variante", max_length=100, blank=True)

    description = models.CharField("Beschreibung", max_length=255)
    notes = models.TextField("Notizen", blank=True)

    # Gross amount + VAT rate - net/VAT amounts are derived, not stored
    # redundantly (see net_amount/vat_amount below).
    amount = models.DecimalField("Betrag (brutto)", max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(
        "USt-Satz (%)", max_digits=4, decimal_places=2, default=Decimal("19.00")
    )

    supplier = models.ForeignKey(
        Supplier, verbose_name="Lieferant", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="expenses",
    )
    supplier_order_number = models.CharField("Bestell-Nr. beim Lieferanten", max_length=100, blank=True)

    invoice_number = models.CharField("Rechnungsnummer", max_length=100, blank=True)
    invoice_date = models.DateField("Rechnungsdatum", blank=True, null=True)
    invoice_file = models.FileField(
        "Rechnung (Datei)", upload_to="documents/finanzen/eingangsrechnungen/", blank=True, null=True
    )

    is_cancelled = models.BooleanField("Storniert", default=False)
    cancelled_at = models.DateField("Storniert am", blank=True, null=True)
    cancellation_invoice_file = models.FileField(
        "Stornorechnung (Datei)", upload_to="documents/finanzen/eingangsrechnungen/storno/", blank=True, null=True
    )

    # Free text, options managed via ReferenceOption(category="payment_account").
    payment_account = models.CharField("Zahlungskonto", max_length=50, blank=True)
    # Free text, options managed via ReferenceOption(category="expense_status").
    status = models.CharField("Status", max_length=50, blank=True, default="Offen")

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Ausgabe"
        verbose_name_plural = "Ausgaben"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.description} ({self.date})"

    @property
    def net_amount(self):
        return self.amount / (1 + self.vat_rate / Decimal("100"))

    @property
    def vat_amount(self):
        return self.amount - self.net_amount

    @property
    def skr03_account(self):
        return AccountMapping.account_for(self.category, self.variant)


class LedgerEntry(models.Model):
    """Mirrors one row of an Etsy statement export - append-only, like a real
    bookkeeping ledger: corrections happen via a new counter-entry, not by
    editing or archiving existing rows."""

    date = models.DateField("Datum")
    # Raw value from Etsy ("Fee", "Sale", "Refund", "Deposit", ...) - kept as
    # free text since Etsy can introduce new types we don't yet know about.
    entry_type = models.CharField("Art", max_length=100)
    title = models.CharField("Titel", max_length=255)
    info = models.CharField("Info", max_length=255, blank=True)

    currency = models.CharField("Währung", max_length=3, default="EUR")
    amount = models.DecimalField("Betrag", max_digits=10, decimal_places=2, blank=True, null=True)
    fees_taxes = models.DecimalField(
        "Gebühren & Steuern", max_digits=10, decimal_places=2, blank=True, null=True
    )
    net = models.DecimalField("Netto", max_digits=10, decimal_places=2, blank=True, null=True)
    tax_info = models.CharField("Steuerliche Angaben", max_length=255, blank=True)

    order = models.ForeignKey(
        Order, verbose_name="Bestellung", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="ledger_entries",
    )
    # Etsy listing id parsed out of Fee rows ("Artikel Nr. X") - not a real FK
    # since the listings CSV carries no matching id (see docs/konzept.md).
    etsy_listing_ref = models.CharField("Etsy-Artikel-Nr.", max_length=100, blank=True)

    SOURCE_IMPORT = "import"
    SOURCE_MANUAL = "manual"
    SOURCE_CHOICES = [(SOURCE_IMPORT, "Import"), (SOURCE_MANUAL, "Manuell")]
    source = models.CharField("Quelle", max_length=10, choices=SOURCE_CHOICES, default=SOURCE_IMPORT)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)

    class Meta:
        verbose_name = "Buchung"
        verbose_name_plural = "Buchungen"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} {self.entry_type} {self.amount}"

    @property
    def skr03_account(self):
        return AccountMapping.account_for(self.entry_type)
