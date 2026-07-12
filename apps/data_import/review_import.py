"""reviews.json -> Review. Matched to an existing Order via order_id (the
raw Etsy order number - see order_import.py for why Order.order_id holds
that value directly). Reviews for orders that haven't been imported yet are
skipped, not stub-created, since a Review always needs a real Order."""

import json
from datetime import datetime

from orders.models import Order, Review


class ReviewImportResult:
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.skipped = []


def _parse_date(raw):
    try:
        return datetime.strptime(raw, "%m/%d/%Y").date()
    except (ValueError, TypeError):
        return None


def import_reviews_from_json(file_obj):
    result = ReviewImportResult()
    data = json.load(file_obj)

    for index, entry in enumerate(data, start=1):
        order_id = str(entry.get("order_id") or "").strip()
        order = Order.objects.filter(order_id=order_id).first()
        if order is None:
            result.skipped.append((index, f"Bestellung {order_id} nicht gefunden"))
            continue

        date_reviewed = _parse_date(entry.get("date_reviewed"))
        if date_reviewed is None:
            result.skipped.append((index, f"Bestellung {order_id}: ungültiges Bewertungsdatum"))
            continue

        reviewer_name = (entry.get("reviewer") or "").strip()
        message = (entry.get("message") or "").strip()
        star_rating = entry.get("star_rating") or 0

        # No stable external id for a review - match on its natural key so
        # re-importing the same export doesn't create duplicates, while two
        # genuinely different reviews on the same order stay distinct.
        review = Review.objects.filter(
            order=order, reviewer_name=reviewer_name, date_reviewed=date_reviewed, message=message
        ).first()
        if review is None:
            Review.objects.create(
                order=order, reviewer_name=reviewer_name, date_reviewed=date_reviewed,
                star_rating=star_rating, message=message,
            )
            result.created += 1
        else:
            review.star_rating = star_rating
            review.save(update_fields=["star_rating"])
            result.updated += 1

    return result
