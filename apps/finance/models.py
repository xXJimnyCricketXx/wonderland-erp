from decimal import Decimal

from django.db import models

from contacts.models import Customer, Supplier
from core.models import Archivable
from orders.models import Order


def income_invoice_path(instance, filename):
    # invoice_date ist bei Income Pflicht (anders als bei Expense unten).
    return f"documents/finanzen/ausgangsrechnungen/{instance.invoice_date.year}/{filename}"


def expense_invoice_path(instance, filename):
    reference_date = instance.invoice_date or instance.date
    year = reference_date.year if reference_date else "unbekannt"
    return f"documents/finanzen/eingangsrechnungen/{year}/{filename}"


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


class Income(Archivable):
    """Manually recorded income outside the Etsy order flow (Order/
    LedgerEntry already cover Etsy sales) - e.g. a private/cash sale not run
    through Etsy, interest, or other one-off income. Kein SKR03-Bezug (anders
    als Expense) - Erlöskonten werden für Einnahmen bewusst nicht angezeigt.
    Storno-Rechnungen (Gutschriften) werden als eigene Income-Zeile mit
    negativem Rechnungsbetrag erfasst, nicht als Expense."""

    # Nicht mehr im Formular - wird beim Speichern automatisch aus
    # invoice_date uebernommen (siehe save()), da es im Formular keinen
    # eigenen Zweck mehr hat und nur noch fuers Filtern (Dashboard/Berichte)
    # gebraucht wird.
    date = models.DateField("Datum")

    # Free text, options managed via ReferenceOption(category="income_category").
    category = models.CharField("Kategorie", max_length=100)

    notes = models.TextField("Notizen", blank=True)

    amount = models.DecimalField("Rechnungsbetrag (brutto)", max_digits=10, decimal_places=2)
    VAT_RATE_CHOICES = [(0, "0%"), (7, "7%"), (19, "19%")]
    vat_rate = models.PositiveSmallIntegerField("USt-Satz", choices=VAT_RATE_CHOICES, default=19)

    # Optional - manuell erfasste Einnahmen (z.B. Barverkauf) haben keine
    # Bestellung. Ist eine Bestellung verknüpft, wird Kunde im Formular per
    # JS automatisch von deren Kunde übernommen (bleibt aber ein normales,
    # überschreibbares Feld - siehe _income_modal.html).
    order = models.ForeignKey(
        Order, verbose_name="Bestellung", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="incomes",
    )
    customer = models.ForeignKey(
        Customer, verbose_name="Kunde", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="incomes",
    )

    invoice_number = models.CharField("Rechnungsnummer", max_length=100)
    invoice_date = models.DateField("Rechnungsdatum")
    invoice_file = models.FileField(
        "Rechnung (Datei)", upload_to=income_invoice_path, blank=True, null=True
    )

    # Free text, options managed via ReferenceOption(category="income_payment_method")
    # - wie der Kunde bezahlt hat (PayPal/Überweisung/Etsy Payments/Bar),
    # nicht zu verwechseln mit payment_account (unser eigenes Konto).
    payment_method = models.CharField("Zahlungsart", max_length=50, blank=True)
    paid_date = models.DateField("Geldeingang", blank=True, null=True)
    # Free text, options managed via ReferenceOption(category="payment_account").
    payment_account = models.CharField("Zahlungskonto", max_length=50, blank=True)
    # Free text, options managed via ReferenceOption(category="income_status")
    # - Einnahmen-exclusive (Expense has its own "expense_status" category).
    status = models.CharField("Status", max_length=50, blank=True, default="Offen")

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Einnahme"
        verbose_name_plural = "Einnahmen"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.invoice_number} ({self.date})"

    def save(self, *args, **kwargs):
        self.date = self.invoice_date
        super().save(*args, **kwargs)

    @property
    def net_amount(self):
        return self.amount / (1 + Decimal(self.vat_rate) / Decimal("100"))

    @property
    def vat_amount(self):
        return self.amount - self.net_amount


class Expense(Archivable):
    """Ausgaben-Erfassung mit Fremdwährungs-Umrechnung und USt-Aufschlüsselung
    nach Satz, damit eine einzelne Rechnung mit gemischten Steuersätzen (z.B.
    7% Bücher + 19% Zubehör) korrekt abgebildet werden kann, statt nur einen
    einzigen pauschalen USt-Satz je Ausgabe anzunehmen."""

    # Sequential "A-0001" id, assigned once on first save - same scheme as
    # Order.order_id's "B-0001" (see orders.models.Order).
    expense_id = models.CharField("Ausgaben-ID", max_length=20, unique=True, blank=True)

    date = models.DateField("Datum")

    # Free text, options managed via ReferenceOption(category="expense_category")
    # - matches AccountMapping.art for the SKR03 lookup.
    category = models.CharField("Art", max_length=100)
    variant = models.CharField("Variante", max_length=100, blank=True)

    description = models.CharField("Beschreibung", max_length=255, blank=True)
    notes = models.TextField("Notizen", blank=True)

    supplier = models.ForeignKey(
        Supplier, verbose_name="Lieferant", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="expenses",
    )

    is_eu = models.BooleanField("EU", default=False)
    is_third_country = models.BooleanField("Drittland", default=False)

    # Free text, options managed via ReferenceOption(category="expense_payment_method")
    # - deliberately its own category, not shared with Order's "payment_method".
    payment_method = models.CharField("Zahlungsart", max_length=50, blank=True)
    paid_date = models.DateField("Zahlungsdatum (Bezahlt)", blank=True, null=True)
    # Free text, options managed via ReferenceOption(category="expense_status")
    # - Ausgaben-exclusive (Income has its own "income_status" category).
    status = models.CharField("Status", max_length=50, blank=True, default="Offen")

    invoice_number = models.CharField("Rechnungsnummer", max_length=100, blank=True)
    invoice_date = models.DateField("Rechnungsdatum", blank=True, null=True)
    invoice_file = models.FileField(
        "Rechnung (Datei)", upload_to=expense_invoice_path, blank=True, null=True
    )

    # --- Betrag & FX ---
    amount = models.DecimalField("Betrag (Original)", max_digits=12, decimal_places=2)
    currency = models.CharField("Währung (Original)", max_length=3, default="EUR")
    fx_rate_eur_per_original = models.DecimalField(
        "FX-Kurs (EUR je 1 Original)", max_digits=14, decimal_places=6, default=Decimal("1"), blank=True
    )
    fx_rate_original_per_eur = models.DecimalField(
        "FX-Kurs (Original je 1 EUR)", max_digits=14, decimal_places=6, default=Decimal("1"), blank=True
    )
    fx_fee_percent = models.DecimalField("FX-Gebühr (%)", max_digits=5, decimal_places=2, default=0, blank=True)
    fx_fee_fixed_eur = models.DecimalField("FX-Gebühr Fix (EUR)", max_digits=10, decimal_places=2, default=0, blank=True)
    # Rechnungsbetrag (EUR), FX-Gebühr (EUR, berechnet), Netto/USt/Brutto
    # Gesamt (EUR) und Konto-Belastung (Soll, EUR) sind bewusst KEINE
    # Datenbankfelder - alle werden aus amount/fx_rate/gross_X/vat_rate
    # berechnet (siehe Properties unten), damit nie zwei widersprüchliche
    # Werte für dieselbe Zahl im Formular stehen können.

    VAT_RATE_CHOICES = [(0, "0%"), (7, "7%"), (19, "19%")]
    vat_rate = models.PositiveSmallIntegerField("USt-Satz", choices=VAT_RATE_CHOICES, default=19)

    # --- USt-Aufschlüsselung ---
    # Nur der Brutto-Betrag je Satz wird erfasst - Netto und "USt (lt.
    # Rechnung)" werden für den unter vat_rate gewählten Satz automatisch aus
    # dem jeweiligen Brutto-Betrag errechnet (siehe net_7/vat_7_invoice/
    # net_19/vat_19_invoice unten). Alle drei Brutto-Felder bleiben editierbar,
    # falls eine Rechnung ausnahmsweise mehrere Sätze gleichzeitig enthält.
    gross_7 = models.DecimalField("Brutto 7%", max_digits=10, decimal_places=2, default=0, blank=True)
    gross_19 = models.DecimalField("Brutto 19%", max_digits=10, decimal_places=2, default=0, blank=True)
    gross_0 = models.DecimalField("Brutto 0%", max_digits=10, decimal_places=2, default=0, blank=True)

    # --- Kontobelastung ---
    account_debit_actual_eur = models.DecimalField(
        "Konto-Belastung (Ist, EUR)", max_digits=12, decimal_places=2, blank=True, null=True
    )

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    class Meta:
        verbose_name = "Ausgabe"
        verbose_name_plural = "Ausgaben"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.expense_id} - {self.description}"

    def save(self, *args, **kwargs):
        if not self.expense_id:
            last = Expense.objects.exclude(expense_id="").order_by("-expense_id").first()
            next_number = 1
            if last:
                try:
                    next_number = int(last.expense_id.split("-")[1]) + 1
                except (ValueError, IndexError):
                    pass
            self.expense_id = f"A-{next_number:04d}"
        super().save(*args, **kwargs)

    @property
    def amount_eur(self):
        """Rechnungsbetrag (EUR) - Original-Betrag umgerechnet zum FX-Kurs."""
        return self.amount * self.fx_rate_eur_per_original

    @property
    def fx_fee_calculated_eur(self):
        return (self.amount_eur * self.fx_fee_percent / Decimal("100")) + self.fx_fee_fixed_eur

    @property
    def net_7(self):
        if self.vat_rate != 7:
            return Decimal("0")
        return self.gross_7 / Decimal("1.07")

    @property
    def vat_7_invoice(self):
        return self.gross_7 - self.net_7

    @property
    def vat_7(self):
        return self.vat_7_invoice

    @property
    def net_19(self):
        if self.vat_rate != 19:
            return Decimal("0")
        return self.gross_19 / Decimal("1.19")

    @property
    def vat_19_invoice(self):
        return self.gross_19 - self.net_19

    @property
    def vat_19(self):
        return self.vat_19_invoice

    @property
    def net_0(self):
        # 0 % USt: Netto entspricht immer dem Brutto-Betrag.
        return self.gross_0

    @property
    def net_total_eur(self):
        return self.net_7 + self.net_19 + self.net_0

    @property
    def vat_total_eur(self):
        return self.vat_7 + self.vat_19

    @property
    def gross_total_eur(self):
        return self.gross_7 + self.gross_19 + self.gross_0

    @property
    def account_debit_target_eur(self):
        """Konto-Belastung (Soll, EUR) - Rechnungsbetrag (EUR) plus die
        berechnete FX-Gebühr, also die erwartete Kontobelastung."""
        return self.amount_eur + self.fx_fee_calculated_eur

    @property
    def account_debit_deviation(self):
        if self.account_debit_actual_eur is None:
            return None
        return self.account_debit_actual_eur - self.account_debit_target_eur

    @property
    def account_debit_display(self):
        """Best-known account-debit figure for list display - the actual
        (reconciled) amount once known, otherwise the planned/target one."""
        return self.account_debit_actual_eur if self.account_debit_actual_eur is not None else self.account_debit_target_eur

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


def tax_report_path(instance, filename):
    return f"documents/finanzen/ust-berichte/{instance.year}/{filename}"


# Feste Werte statt Freitext, jeweils mit fortlaufendem Sortier-Code, damit
# "-year", "-period" eine echte chronologische Liste ergibt (neuester Bericht
# oben) statt der alphabetischen Sortierung von vorher (die z.B. "Oktober"
# vor "September" einordnete).
PERIOD_CHOICES = [
    (1, "Januar"), (2, "Februar"), (3, "März"), (4, "April"),
    (5, "Mai"), (6, "Juni"), (7, "Juli"), (8, "August"),
    (9, "September"), (10, "Oktober"), (11, "November"), (12, "Dezember"),
    (13, "Q1 (Jan-Mrz)"), (14, "Q2 (Apr-Jun)"), (15, "Q3 (Jul-Sep)"), (16, "Q4 (Okt-Dez)"),
    (17, "Jahresbericht"),
]


class TaxReport(models.Model):
    """Periodische USt-/Steuerberichte, die Etsy als PDF bereitstellt - nicht
    an eine einzelne Bestellung/Ausgabe/Einnahme gebunden, daher ein eigenes
    kleines Modell (mirrors PackagingLicenseDocument in knowledge/models.py)."""

    year = models.PositiveIntegerField("Jahr")
    # null=True nur fuer die Migration von alten Freitext-Eintraegen, die
    # sich nicht zuverlaessig automatisch zuordnen lassen (siehe Migration) -
    # das Formular verlangt trotzdem immer einen Wert fuer neue/bearbeitete
    # Eintraege.
    period = models.PositiveSmallIntegerField("Zeitraum", choices=PERIOD_CHOICES, null=True, blank=True)
    file = models.FileField("Datei", upload_to=tax_report_path)
    uploaded_at = models.DateTimeField("Hochgeladen am", auto_now_add=True)

    class Meta:
        verbose_name = "USt-Bericht"
        verbose_name_plural = "USt-Berichte"
        ordering = ["-year", "-period"]

    def __str__(self):
        return f"{self.get_period_display() or '?'} {self.year}"
