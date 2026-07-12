"""Shared helper for both order_import.py and article_import.py: Etsy's own
SKU-ish fields (order "SKU" column, listing "BESTANDSEINHEIT" column) have
historically been used as a supplier hint (e.g. "WELSCH", "LIND") rather
than a real SKU/inventory code - see docs/konzept.md."""

from contacts.models import Supplier


def match_supplier(token):
    token = (token or "").strip()
    if not token:
        return None
    return (
        Supplier.objects.filter(last_name__iexact=token).first()
        or Supplier.objects.filter(first_name__iexact=token).first()
        or Supplier.objects.filter(company_name__iexact=token).first()
        or Supplier.objects.filter(company_name__istartswith=token).first()
    )
