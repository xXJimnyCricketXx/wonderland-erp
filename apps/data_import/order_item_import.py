"""Etsy "Sold Order Items"-CSV -> OrderItem (real item name/listing id/
variation/quantity/price instead of just the raw SKU hint). Depends on the
matching Order already existing (imported via order_import.py first, same
Order ID) - rows for an unknown order are skipped rather than creating a
partial Order, since this file alone doesn't carry the order-level fields
(payment, status, fees, ...) order_import.py needs.

listing_id is the actual point of this import: it's Etsy's stable per-
listing id, so a single EtsyListingMapping entry (see catalog.models) can
apply to every past and future order of that listing - see
apply_listing_mappings() below."""

import csv
import html
import io
from decimal import Decimal, InvalidOperation

from catalog.models import EtsyListingMapping
from orders.models import Order, OrderItem


def _clean(raw):
    return html.unescape((raw or "").strip())


def _parse_decimal(raw):
    raw = _clean(raw)
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def _parse_int(raw, default=1):
    try:
        return int(_clean(raw))
    except ValueError:
        return default


class OrderItemImportResult:
    def __init__(self):
        self.orders_updated = 0
        self.items_created = 0
        self.listings_seen = 0
        self.skipped = []


def import_order_items_from_csv(file_obj):
    result = OrderItemImportResult()
    decoded = io.TextIOWrapper(file_obj, encoding="utf-8")
    reader = csv.DictReader(decoded)

    rows_by_order = {}
    for line_number, row in enumerate(reader, start=2):
        etsy_order_id = _clean(row.get("Order ID"))
        if not etsy_order_id:
            result.skipped.append((line_number, "Keine Order ID"))
            continue
        rows_by_order.setdefault(etsy_order_id, []).append(row)

    for etsy_order_id, rows in rows_by_order.items():
        order = Order.objects.filter(etsy_order_number=etsy_order_id).first()
        if order is None:
            result.skipped.append((
                None,
                f"Bestellung {etsy_order_id} nicht gefunden - bitte zuerst die "
                f"Sold-Orders-CSV für diesen Zeitraum importieren.",
            ))
            continue

        order.items.all().delete()
        for position, row in enumerate(rows, start=1):
            listing_id = _clean(row.get("Listing ID"))
            item_name = _clean(row.get("Item Name"))

            article = None
            if listing_id:
                mapping, created = EtsyListingMapping.objects.get_or_create(
                    listing_id=listing_id, defaults={"item_name": item_name}
                )
                if not created and item_name and mapping.item_name != item_name:
                    mapping.item_name = item_name
                    mapping.save(update_fields=["item_name"])
                article = mapping.article
                if created:
                    result.listings_seen += 1

            OrderItem.objects.create(
                order=order,
                article=article,
                item_name=item_name,
                listing_id=listing_id,
                variations=_clean(row.get("Variations")),
                quantity=_parse_int(row.get("Quantity")),
                price=_parse_decimal(row.get("Price")),
                sku_raw=_clean(row.get("SKU")),
                position=position,
            )
            result.items_created += 1

        result.orders_updated += 1

    return result
