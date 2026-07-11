"""Config-driven registry for the global Papierkorb (trash) in Einstellungen -
one entry per Archivable model, so restore/hard-delete/empty views and the
template can all stay generic instead of duplicating per-model code."""

from catalog.models import Article
from contacts.models import Customer, Supplier
from orders.models import Order
from tasks.models import Task

TRASH_REGISTRY = [
    {
        "slug": "artikel",
        "label": "Artikel",
        "model": Article,
        "fields": [("SKU", "sku"), ("Titel", "title")],
        "base_filter": {"parent_article__isnull": True},
    },
    {
        "slug": "kunden",
        "label": "Kunden",
        "model": Customer,
        "fields": [("Name", "full_name"), ("E-Mail", "email")],
        "base_filter": {},
    },
    {
        "slug": "lieferanten",
        "label": "Lieferanten",
        "model": Supplier,
        "fields": [("Name", "full_name"), ("E-Mail", "email")],
        "base_filter": {},
    },
    {
        "slug": "bestellungen",
        "label": "Bestellungen",
        "model": Order,
        "fields": [("Bestell-ID", "order_id"), ("Kunde", "customer")],
        "base_filter": {},
    },
    {
        "slug": "aufgaben",
        "label": "Aufgaben",
        "model": Task,
        "fields": [("Titel", "title"), ("Fällig am", "due_date")],
        "base_filter": {},
    },
]

TRASH_REGISTRY_BY_SLUG = {entry["slug"]: entry for entry in TRASH_REGISTRY}
