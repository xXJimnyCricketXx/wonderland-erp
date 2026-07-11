"""Known Referenzdaten categories: display labels (for the settings UI) and
default seed values (for seed_reference_data). Adding a brand-new category
straight from the settings page still works - it just falls back to showing
its raw slug as the label until it's added here."""

CATEGORY_LABELS = {
    "article_category": "Artikel-Kategorien",
    "contact_status": "Kontakt-Status",
    "preferred_contact_method": "Bevorzugte Kontaktart",
    "wishlist_status": "Wunschlisten-Status",
    "wishlist_tag": "Wunschlisten-Tags",
    "task_tag": "Aufgaben-Tags",
    "expense_category": "Ausgaben-Kategorien",
    "payment_account": "Zahlungskonto",
    "expense_status": "Ausgaben-Status",
    "vat_rate": "USt-Sätze",
    "order_status": "Bestell-Status",
    "order_type": "Bestellart",
    "payment_method": "Zahlungsmethode",
    "payment_type": "Zahlungsart",
}

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
}
