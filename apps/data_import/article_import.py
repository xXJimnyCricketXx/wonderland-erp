"""Etsy "Listings"-CSV -> Article. Matches existing rows by exact title
(there's no reliable SKU to match on - see Article.sku's docstring), so
re-running the import on an updated export is safe and just refreshes
price/description/stock instead of creating duplicates.

BESTANDSEINHEIT (Etsy's own per-listing inventory/SKU field) is likewise not
used as Article.sku - the shop has historically written supplier codes
there instead (e.g. "WELSCH", "LIND"), so it's used only to look up and
fill in Article.supplier where it matches an existing Supplier contact."""

import csv
import html
import io
from decimal import Decimal, InvalidOperation

from catalog.models import Article

from .supplier_matching import match_supplier

# Etsy only gives one STÜCKZAHL for the whole listing, not per variation
# combination, so per-variant stock can't be derived from the CSV - variants
# are created with stock_quantity=0 for manual entry afterwards.
VARIATION_COLUMN_PAIRS = [
    ("VARIATIONSNAME 1", "VARIATIONSWERT 1"),
    ("VARIATIONSNAME 2", "VARIATIONSWERT 2"),
]


class ArticleImportResult:
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.variants_created = 0
        self.variants_updated = 0
        self.skipped = []

    @property
    def total_rows(self):
        return self.created + self.updated + len(self.skipped)


def _clean(raw):
    return html.unescape((raw or "").strip())


def _parse_decimal(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        try:
            return Decimal(raw.replace(".", "").replace(",", "."))
        except InvalidOperation:
            return None


def _parse_int(raw, default=0):
    try:
        return int((raw or "").strip())
    except ValueError:
        return default


def import_articles_from_csv(file_obj):
    result = ArticleImportResult()
    decoded = io.TextIOWrapper(file_obj, encoding="utf-8")
    reader = csv.DictReader(decoded)

    for line_number, row in enumerate(reader, start=2):
        title = _clean(row.get("TITEL"))
        if not title:
            result.skipped.append((line_number, "Kein Titel"))
            continue

        price = _parse_decimal(row.get("PREIS"))
        if price is None:
            result.skipped.append((line_number, f'"{title}": kein gültiger Preis'))
            continue

        description = _clean(row.get("BESCHREIBUNG"))
        currency_code = _clean(row.get("WÄHRUNGSCODE")) or "EUR"
        stock_quantity = _parse_int(row.get("STÜCKZAHL"))
        thumbnail_url = (row.get("BILD1") or "").strip()
        supplier = match_supplier(row.get("BESTANDSEINHEIT"))

        article = Article.objects.filter(title=title, parent_article__isnull=True).first()
        created = article is None
        if created:
            article = Article(title=title)
        article.description = description
        article.price = price
        article.currency_code = currency_code
        article.stock_quantity = stock_quantity
        article.thumbnail_url = thumbnail_url
        if supplier:
            article.supplier = supplier
        article.save()

        if created:
            result.created += 1
        else:
            result.updated += 1

        variant_labels = []
        for name_column, value_column in VARIATION_COLUMN_PAIRS:
            variation_name = _clean(row.get(name_column))
            values_raw = row.get(value_column) or ""
            for value in values_raw.split(","):
                value = _clean(value)
                if not value:
                    continue
                variant_labels.append(f"{variation_name}: {value}" if variation_name else value)

        for label in variant_labels:
            variant = Article.objects.filter(parent_article=article, variant_label=label).first()
            v_created = variant is None
            if v_created:
                variant = Article(parent_article=article, variant_label=label)
            variant.title = title
            variant.description = description
            variant.price = price
            variant.currency_code = currency_code
            variant.thumbnail_url = thumbnail_url
            if supplier:
                variant.supplier = supplier
            variant.save()

            if v_created:
                result.variants_created += 1
            else:
                result.variants_updated += 1

    return result
