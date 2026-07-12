"""Known Referenzdaten categories: display labels (for the settings UI) and
default seed values (for seed_reference_data). Adding a brand-new category
straight from the settings page still works - it just falls back to showing
its raw slug as the label until it's added here."""

CATEGORY_LABELS = {
    "article_category": "Artikel-Kategorien",
    "contact_status": "Kontakt-Status",
    "preferred_contact_method": "Bevorzugte Kontaktart",
    "wishlist_status": "Inspirationboard-Status",
    "wishlist_tag": "Inspirationboard-Tags",
    "task_tag": "Aufgaben-Tags",
    "expense_category": "Ausgaben-Kategorien",
    "payment_account": "Zahlungskonto",
    "expense_status": "Ausgaben-Status",
    "vat_rate": "USt-Sätze",
    "order_status": "Bestell-Status",
    "order_type": "Bestellart",
    "payment_method": "Zahlungsmethode",
    "payment_type": "Zahlungsart",
    "appointment_type": "Termin-Typ",
    "shipping_payment_method": "Versand-Bezahlen",
}

# Groups the Referenzdaten UI by the menu section each category belongs to
# (same order/icons as the sidebar) so it's easy to find "which dropdown
# feeds which page". A category not listed here still shows up, just under
# the catch-all "Sonstiges" group at the end - see settings_hub/views.py.
CATEGORY_GROUPS = [
    {"slug": "artikel", "label": "Artikel", "icon": "bi-box-seam", "categories": ["article_category"]},
    {
        "slug": "bestellungen", "label": "Bestellungen", "icon": "bi-cart3",
        "categories": ["order_status", "order_type", "payment_method", "payment_type"],
    },
    {
        "slug": "kontakte", "label": "Kontakte", "icon": "bi-people",
        "categories": ["contact_status", "preferred_contact_method"],
    },
    {
        "slug": "finanzen", "label": "Finanzen", "icon": "bi-cash-coin",
        "categories": ["expense_category", "payment_account", "expense_status", "vat_rate"],
    },
    {"slug": "aufgaben", "label": "Aufgaben", "icon": "bi-check2-square", "categories": ["task_tag"]},
    {"slug": "termine", "label": "Termine", "icon": "bi-calendar3", "categories": ["appointment_type"]},
    {"slug": "infothek", "label": "Infothek", "icon": "bi-journal-text", "categories": ["shipping_payment_method"]},
    {
        "slug": "wunschliste", "label": "Inspirationboard", "icon": "bi-heart",
        "categories": ["wishlist_status", "wishlist_tag"],
    },
]

DEFAULT_SEED_DATA = {
    "contact_status": ["Aktiv", "Lead", "Pausiert", "Abgeschlossen"],
    "preferred_contact_method": ["E-Mail", "Telefon", "Etsy-Nachricht", "Post"],
    "wishlist_status": ["Idee", "In Erwägung", "Bestellt", "Verworfen"],
    "expense_category": [
        "Handelsware", "Verbrauchsware", "Porto", "Büro", "Kleinzeug",
        "GWG", "Deko/Werbung", "Gebühren", "Sonstiges",
    ],
    "payment_account": ["Bank", "Kasse", "KG", "Bank-Direktkauf"],
    "expense_status": ["Offen", "Bezahlt"],
    "vat_rate": ["0", "7", "19"],
    "order_status": ["Zahlung ausstehend", "Bezahlt", "Versendet", "Abgeschlossen", "Storniert", "Rückerstattet"],
    "order_type": ["Etsy", "Barverkauf"],
    "payment_method": ["Etsy Payments", "PayPal", "Überweisung", "Bar"],
    "payment_type": ["Kreditkarte", "PayPal-Guthaben", "Sofortüberweisung", "Bar"],
    "appointment_type": ["Meeting", "Markt", "Lieferung", "Beratung", "Sonstiges"],
    "shipping_payment_method": ["Online-Frankierung", "Rechnung", "Guthaben", "Filiale"],
}
