"""Etsy-Statement (Zahlungskonto-Abrechnung) CSV -> LedgerEntry. Append-only
mirror of Etsy's own ledger export, matching LedgerEntry's own "corrections
happen via a new counter-entry, not by editing" philosophy - re-running the
same export is safe (rows are matched on their own natural key and skipped
if already present), so accidentally importing an overlapping date range
twice doesn't create duplicates.

Etsy's date column ("29. June 2026") uses English month names regardless of
the account's locale - parsed with an explicit month-name lookup rather than
strptime's locale-dependent %B, so this doesn't break on a machine set to a
different locale. Money columns use "--" as their "no value" placeholder and
put the minus sign before the € symbol for negative amounts (e.g. "-€13.90")."""

import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from finance.models import LedgerEntry
from orders.models import Order

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}
DATE_RE = re.compile(r"(\d{1,2})\.\s*(\w+)\s*(\d{4})")
ORDER_NUMBER_RE = re.compile(r"Order #(\d+)")
LISTING_REF_RE = re.compile(r"Artikel Nr\.\s*(\d+)")


class StatementImportResult:
    def __init__(self):
        self.created = 0
        self.skipped_duplicates = 0
        self.errors = []


def _parse_date(raw):
    match = DATE_RE.match((raw or "").strip())
    if not match:
        return None
    day, month_name, year = match.groups()
    month = MONTHS.get(month_name)
    if not month:
        return None
    try:
        return date(int(year), month, int(day))
    except ValueError:
        return None


def _parse_money(raw):
    raw = (raw or "").strip()
    if raw in ("", "--"):
        return None
    try:
        return Decimal(raw.replace("€", "").replace(",", ""))
    except InvalidOperation:
        return None


def import_statement_from_csv(file_obj):
    result = StatementImportResult()
    decoded = io.TextIOWrapper(file_obj, encoding="utf-8-sig")
    reader = csv.DictReader(decoded)

    for line_number, row in enumerate(reader, start=2):
        entry_date = _parse_date(row.get("Datum"))
        if entry_date is None:
            result.errors.append((line_number, f"Ungültiges Datum: {row.get('Datum')!r}"))
            continue

        entry_type = (row.get("Art") or "").strip()
        title = (row.get("Titel") or "").strip()
        info = (row.get("Info") or "").strip()
        currency = (row.get("Währung") or "EUR").strip()
        amount = _parse_money(row.get("Betrag"))
        fees_taxes = _parse_money(row.get("Gebühren & Steuern"))
        net = _parse_money(row.get("Netto"))
        tax_info_raw = (row.get("Steuerliche Angaben") or "").strip()
        tax_info = "" if tax_info_raw == "--" else tax_info_raw

        order_match = ORDER_NUMBER_RE.search(title) or ORDER_NUMBER_RE.search(info)
        order = Order.objects.filter(etsy_order_number=order_match.group(1)).first() if order_match else None

        listing_match = LISTING_REF_RE.search(info)
        etsy_listing_ref = listing_match.group(1) if listing_match else ""

        # No stable per-row id in the export - match on the natural key of
        # everything that identifies a unique row instead (same approach as
        # review_import.py), so a repeat/overlapping import is a no-op.
        exists = LedgerEntry.objects.filter(
            date=entry_date, entry_type=entry_type, title=title, info=info,
            amount=amount, fees_taxes=fees_taxes,
        ).exists()
        if exists:
            result.skipped_duplicates += 1
            continue

        LedgerEntry.objects.create(
            date=entry_date, entry_type=entry_type, title=title, info=info, currency=currency,
            amount=amount, fees_taxes=fees_taxes, net=net, tax_info=tax_info,
            order=order, etsy_listing_ref=etsy_listing_ref, source=LedgerEntry.SOURCE_IMPORT,
        )
        result.created += 1

    return result
