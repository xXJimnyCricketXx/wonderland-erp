"""Etsy "Sold Orders"-CSV -> Order (+ Customer, + OrderItem).

Order.order_id is the internal "B-0001, B-0002, ..." sequence (oldest
sale_date first), NOT Etsy's own order number - that one lives in
etsy_order_number, which is also the match key used to find an existing
Order on re-import (idempotent). New orders get Etsy's raw order id as a
*temporary* order_id placeholder (still unique) until assign_order_ids()
renumbers everything without a "B-" id into the real sequence at the end
of the import - see that function for why numbering isn't just done
per-row here (CSV row order isn't reliably chronological).

The SKU column is NOT used to match Article - historically unreliable, see
Article.sku's docstring and OrderItem.sku_raw's comment - it's kept only as
OrderItem.sku_raw for later reference.
"""

import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from contacts.models import Customer
from orders.models import Order, OrderItem


def _clean(raw):
    return (raw or "").strip()


def _parse_date(raw):
    raw = _clean(raw)
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%m/%d/%y").date()
    except ValueError:
        return None


def _parse_decimal(raw, default=Decimal("0")):
    raw = _clean(raw)
    if not raw:
        return default
    try:
        return Decimal(raw)
    except InvalidOperation:
        return default


def _parse_decimal_or_none(raw):
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


class OrderImportResult:
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.customers_created = 0
        self.order_ids_assigned = 0
        self.skipped = []


def assign_order_ids():
    """Gives every Order without a real "B-XXXX" order_id the next one in
    sequence, oldest sale_date first - continues after the highest existing
    B-number rather than restarting, so it's safe to call repeatedly (e.g.
    once per CSV import) without disturbing already-assigned ids."""
    existing_max = 0
    for order_id in Order.objects.filter(order_id__startswith="B-").values_list("order_id", flat=True):
        suffix = order_id[2:]
        if suffix.isdigit():
            existing_max = max(existing_max, int(suffix))
    next_number = existing_max + 1

    to_number = Order.objects.exclude(order_id__startswith="B-").order_by("sale_date", "etsy_order_number")
    assigned = 0
    for order in to_number:
        order.order_id = f"B-{next_number:04d}"
        order.save(update_fields=["order_id"])
        next_number += 1
        assigned += 1
    return assigned


def _get_or_create_customer(row):
    first_name = _clean(row.get("First Name"))
    last_name = _clean(row.get("Last Name"))
    buyer_user_id = _clean(row.get("Buyer User ID"))

    customer = None
    if buyer_user_id:
        customer = Customer.objects.filter(etsy_buyer_user_id=buyer_user_id).first()
    if customer is None:
        customer = Customer.objects.filter(
            first_name=first_name, last_name=last_name, etsy_buyer_user_id__isnull=True
        ).first()

    created = customer is None
    if created:
        customer = Customer(first_name=first_name or "Unbekannt", last_name=last_name)

    if buyer_user_id:
        customer.etsy_buyer_user_id = buyer_user_id
    # Only fill in address on first sight - later orders shouldn't overwrite
    # a customer's real/current address with an older shipping address.
    if not customer.street1:
        customer.street1 = _clean(row.get("Street 1"))
        customer.street2 = _clean(row.get("Street 2"))
        customer.city = _clean(row.get("Ship City"))
        customer.state = _clean(row.get("Ship State"))
        customer.zipcode = _clean(row.get("Ship Zipcode"))
        customer.country = _clean(row.get("Ship Country"))
    customer.save()
    return customer, created


def import_orders_from_csv(file_obj):
    result = OrderImportResult()
    decoded = io.TextIOWrapper(file_obj, encoding="utf-8")
    reader = csv.DictReader(decoded)

    for line_number, row in enumerate(reader, start=2):
        etsy_order_id = _clean(row.get("Order ID"))
        if not etsy_order_id:
            result.skipped.append((line_number, "Keine Order ID"))
            continue

        sale_date = _parse_date(row.get("Sale Date"))
        if sale_date is None:
            result.skipped.append((line_number, f"Order {etsy_order_id}: kein gültiges Verkaufsdatum"))
            continue

        customer, customer_created = _get_or_create_customer(row)
        if customer_created:
            result.customers_created += 1

        order = Order.objects.filter(etsy_order_number=etsy_order_id).first()
        created = order is None
        if created:
            # Temporary placeholder - assign_order_ids() below replaces this
            # with the real "B-XXXX" id, sorted by sale_date across the
            # whole import (not just this row's position in the CSV).
            order = Order(order_id=etsy_order_id)

        order.etsy_order_number = etsy_order_id
        order.customer = customer
        order.sale_date = sale_date
        order.date_shipped = _parse_date(row.get("Date Shipped"))
        order.number_of_items = _parse_int(row.get("Number of Items"), default=1)
        order.payment_method = _clean(row.get("Payment Method"))
        order.status = _clean(row.get("Status"))
        order.buyer_username = _clean(row.get("Buyer"))
        order.order_type = _clean(row.get("Order Type"))
        order.payment_type = _clean(row.get("Payment Type"))

        order.ship_street1 = _clean(row.get("Street 1"))
        order.ship_street2 = _clean(row.get("Street 2"))
        order.ship_city = _clean(row.get("Ship City"))
        order.ship_state = _clean(row.get("Ship State"))
        order.ship_zipcode = _clean(row.get("Ship Zipcode"))
        order.ship_country = _clean(row.get("Ship Country"))

        order.currency = _clean(row.get("Currency")) or "EUR"
        order.order_value = _parse_decimal(row.get("Order Value"))
        order.coupon_code = _clean(row.get("Coupon Code"))
        order.coupon_details = _clean(row.get("Coupon Details"))
        order.discount_amount = _parse_decimal(row.get("Discount Amount"))
        order.shipping_discount = _parse_decimal(row.get("Shipping Discount"))
        order.shipping = _parse_decimal(row.get("Shipping"))
        order.sales_tax = _parse_decimal(row.get("Sales Tax"))
        order.order_total = _parse_decimal(row.get("Order Total"))
        order.card_processing_fees = _parse_decimal(row.get("Card Processing Fees"))
        order.order_net = _parse_decimal(row.get("Order Net"))
        order.adjusted_order_total = _parse_decimal_or_none(row.get("Adjusted Order Total"))
        order.adjusted_card_processing_fees = _parse_decimal_or_none(row.get("Adjusted Card Processing Fees"))
        order.adjusted_net_order_amount = _parse_decimal_or_none(row.get("Adjusted Net Order Amount"))
        order.inperson_discount = _parse_decimal_or_none(row.get("InPerson Discount"))
        order.inperson_location = _clean(row.get("InPerson Location"))

        order.save()

        if created:
            result.created += 1
        else:
            result.updated += 1

        # Always create one OrderItem per number_of_items - even when the SKU
        # column was blank - so the position count matches what the order
        # actually says it contains, instead of silently having zero rows.
        sku_tokens = [t.strip() for t in (row.get("SKU") or "").split(",") if t.strip()]
        item_count = max(order.number_of_items, len(sku_tokens))
        order.items.all().delete()
        for position in range(1, item_count + 1):
            sku_raw = sku_tokens[position - 1] if position <= len(sku_tokens) else ""
            OrderItem.objects.create(order=order, sku_raw=sku_raw, position=position)

    result.order_ids_assigned = assign_order_ids()
    return result
