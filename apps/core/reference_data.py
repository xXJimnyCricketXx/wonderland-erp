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
    "income_category": "Einnahmen-Kategorien",
    "income_status": "Einnahmen-Status",
    "income_payment_method": "Einnahmen-Zahlungsart",
    "expense_category": "Ausgaben-Kategorien",
    "expense_payment_method": "Ausgaben-Zahlungsart",
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
        "categories": [
            "income_category", "income_status", "income_payment_method", "expense_category",
            "expense_payment_method", "payment_account", "expense_status", "vat_rate",
        ],
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
    "income_category": ["Verkauf Bar", "Verkauf sonstige Plattform", "Zinsen", "Sonstige Einnahmen"],
    "income_status": ["Offen", "Bezahlt"],
    "income_payment_method": ["PayPal", "Überweisung", "Etsy Payments", "Bar"],
    # Deckt sich 1:1 mit den "Art"-Werten in der SKR03-Konten-Zuordnung
    # (Referenzdaten → Finanzen → Konten-Zuordnung) - siehe finance/
    # migrations/0009_replace_skr03_seed_data.py (Quelle: testdata/skr03_mapping.json).
    "expense_category": [
        "Waren / Handel", "Waren / Verbrauch", "Verpackung / Porto", "Bürobedarf",
        "Kleinmaterialien / Werkstattbedarf", "GWG", "Dekomaterial / Werbekosten",
        "Gebühren", "Sonstiges", "Reisekosten Unternehmer", "Kfz-Kosten",
        "Telefon/Internet", "Software/EDV", "Fortbildung", "Fachliteratur",
        "Beratungskosten", "Versicherung", "Arbeitszimmer",
        "Betriebsausstattung (Anlagevermögen)",
    ],
    "expense_payment_method": ["Kreditkarte", "PayPal", "Überweisung", "Lastschrift", "Bar"],
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
