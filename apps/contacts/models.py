from datetime import timedelta

from django.db import models
from django.utils import timezone

from core.models import Archivable, ArchivableQuerySet


class ContactQuerySet(ArchivableQuerySet):
    def needs_attention(self, days=30):
        cutoff = timezone.now().date() - timedelta(days=days)
        return self.filter(last_contact_at__lt=cutoff)


class ContactBase(Archivable):
    """Shared fields for Customer/Supplier - abstract, so each subclass gets
    its own table (and its own auto-incrementing id, i.e. Kunden-/
    Lieferanten-Nr.) instead of one shared Contact table with a type flag."""

    first_name = models.CharField("Vorname", max_length=255)
    last_name = models.CharField("Nachname", max_length=255)

    company_name = models.CharField("Firma", max_length=255, blank=True)
    job_title = models.CharField("Position", max_length=255, blank=True)

    street1 = models.CharField("Straße & Hausnummer", max_length=255, blank=True)
    street2 = models.CharField("Adresszusatz", max_length=255, blank=True)
    city = models.CharField("Ort", max_length=255, blank=True)
    state = models.CharField("Bundesland/Region", max_length=255, blank=True)
    zipcode = models.CharField("PLZ", max_length=20, blank=True)
    country = models.CharField("Land", max_length=100, blank=True)

    email = models.EmailField("E-Mail", blank=True)
    phone = models.CharField("Telefon", max_length=50, blank=True)
    # Free text, options managed via ReferenceOption(category="preferred_contact_method")
    # in the Referenzdaten settings screen instead of a hardcoded enum.
    preferred_contact_method = models.CharField("Bevorzugte Kontaktart", max_length=50, blank=True)

    birthday = models.DateField("Geburtstag", blank=True, null=True)
    # Manually maintained, not auto-derived from orders/appointments - see
    # ContactQuerySet.needs_attention() for the >30-days-since check, computed
    # at query time rather than stored as a boolean that could go stale.
    last_contact_at = models.DateField("Letzter Kontakt", blank=True, null=True)
    # Free text, options managed via ReferenceOption(category="contact_status").
    status = models.CharField("Status", max_length=50, blank=True, default="Aktiv")

    notes = models.TextField("Notizen", blank=True)

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)

    objects = ContactQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Customer(ContactBase):
    # Etsy's stable per-buyer identifier - only set for customers imported
    # from order CSVs, blank for ones added manually (e.g. direct sales).
    etsy_buyer_user_id = models.CharField(
        "Etsy-Käufer-ID", max_length=100, blank=True, null=True, unique=True
    )

    # Auto-set to True once this customer has more than one order (see
    # Order.save) - a one-way ratchet, never auto-unset. Can still be
    # flipped manually (e.g. for a customer met in person with no Order
    # records at all).
    is_returning_customer = models.BooleanField("Stammkunde", default=False)

    class Meta(ContactBase.Meta):
        verbose_name = "Kunde"
        verbose_name_plural = "Kunden"


class Supplier(ContactBase):
    # Unlike Customer, a Supplier is often a company with no natural
    # "person" name (e.g. wholesalers imported from order SKU hints like
    # "WELSCH"/"IMPEXCO") - so first/last name are optional here.
    first_name = models.CharField("Vorname", max_length=255, blank=True)
    last_name = models.CharField("Nachname", max_length=255, blank=True)

    website = models.URLField("Website", blank=True)
    # The account number *the supplier* assigned to us - not our own id/PK.
    account_number = models.CharField("Kundennummer beim Lieferanten", max_length=100, blank=True)
    payment_terms = models.CharField("Zahlungsziel", max_length=255, blank=True)
    lead_time_days = models.PositiveIntegerField("Lieferzeit (Tage)", blank=True, null=True)
    vat_id = models.CharField("USt-ID", max_length=50, blank=True)

    # Flat-rate discount case (e.g. "immer 50% Rabatt"). Volume-tiered
    # discounts (e.g. "ab 100€ 10%, ab 300€ 15%") live in SupplierDiscountTier
    # instead, as queryable data rather than a free-text note.
    standard_discount_percent = models.DecimalField(
        "Standard-Rabatt (%)", max_digits=5, decimal_places=2, blank=True, null=True
    )

    # Two-level supplier: "platform" is who you bought through (e.g. Amazon),
    # this row can still be the actual seller/brand (e.g. "shenzhen") linked
    # back to it - mirrors Article.parent_article.
    platform = models.ForeignKey(
        "self", verbose_name="Plattform", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="sellers",
    )

    class Meta(ContactBase.Meta):
        verbose_name = "Lieferant"
        verbose_name_plural = "Lieferanten"

    @property
    def full_name(self):
        # Unlike Customer, prefer the company name when set - a supplier is
        # usually dealt with as a company, not the specific person's name.
        return self.company_name or f"{self.first_name} {self.last_name}".strip()


class SupplierDiscountTier(models.Model):
    supplier = models.ForeignKey(
        Supplier, verbose_name="Lieferant", on_delete=models.CASCADE, related_name="discount_tiers"
    )
    min_order_value = models.DecimalField("Mindestbestellwert", max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField("Rabatt (%)", max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = "Rabattstaffel"
        verbose_name_plural = "Rabattstaffeln"
        ordering = ["supplier", "min_order_value"]

    def __str__(self):
        return f"{self.supplier} ab {self.min_order_value}: {self.discount_percent}%"
