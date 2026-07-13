# Kontonummern/Bezeichnungen entnommen aus testdata/11174 SKR03 BilrUg.pdf
# (DATEV-Kontenrahmen SKR03, Stand 2026) - nur die für die neun Ausgaben-
# Kategorien (siehe core/reference_data.py::DEFAULT_SEED_DATA["expense_category"])
# tatsächlich benötigten Konten, nicht der volle Kontenrahmen.
from django.db import migrations

SKR03_ACCOUNTS = [
    ("0027", "EDV-Software"),
    ("0030", "Lizenzen an gewerblichen Schutzrechten und ähnlichen Rechten und Werten"),
    ("0480", "Geringwertige Wirtschaftsgüter"),
    ("0485", "Wirtschaftsgüter (Sammelposten)"),
    ("3106", "Fremdleistungen 19 % Vorsteuer"),
    ("3108", "Fremdleistungen 7 % Vorsteuer"),
    ("3300", "Wareneingang 7 % Vorsteuer"),
    ("3400", "Wareneingang 19 % Vorsteuer"),
    ("3800", "Bezugsnebenkosten"),
    ("3850", "Zölle und Einfuhrabgaben"),
    ("4600", "Werbekosten"),
    ("4710", "Verpackungsmaterial"),
    ("4730", "Ausgangsfrachten"),
    ("4806", "Wartungskosten für Hard- und Software"),
    ("4830", "Abschreibungen auf Sachanlagen (ohne AfA auf Fahrzeuge und Gebäude)"),
    ("4855", "Sofortabschreibung geringwertiger Wirtschaftsgüter"),
    ("4860", "Abschreibungen auf aktivierte, geringwertige Wirtschaftsgüter"),
    ("4909", "Fremdleistungen/Fremdarbeiten"),
    ("4910", "Porto"),
    ("4930", "Bürobedarf"),
    ("4970", "Nebenkosten des Geldverkehrs"),
    ("4980", "Sonstiger Betriebsbedarf"),
    ("4985", "Werkzeuge und Kleingeräte"),
]

# (art, variante, skr03_nummer) - art entspricht 1:1 den expense_category-
# Referenzwerten. "Waren-Verbrauch" ist bewusst NICHT enthalten - im SKR03
# fällt der Einkauf von Roh-/Hilfsstoffen unter dieselben Wareneingangs-
# konten (3300/3400) wie Waren-Handel, es gibt keine separate Kontonummer
# dafür im Kontenrahmen; siehe Notiz an den Nutzer statt hier zu raten.
ACCOUNT_MAPPINGS = [
    ("Waren-Handel", "7%", "3300"),
    ("Waren-Handel", "19%", "3400"),
    ("Verpackung/Porto", "Porto", "4910"),
    ("Verpackung/Porto", "Verpackungsmaterial", "4710"),
    ("Verpackung/Porto", "Einkauf Fracht", "3800"),
    ("Verpackung/Porto", "Eigene Auslieferung", "4730"),
    ("Verpackung/Porto", "Zoll/Einfuhr", "3850"),
    ("Bürobedarf", "", "4930"),
    ("Kleinmaterialien/Werkstattbedarf", "Werkzeuge/Kleingeräte", "4985"),
    ("Kleinmaterialien/Werkstattbedarf", "Sonstiger Bedarf", "4980"),
    ("GWG", "Sofortabschreibung (bis 800 €)", "4855"),
    ("GWG", "Sammelposten (250-1000 €)", "4860"),
    ("Werbekosten", "", "4600"),
    ("Gebühren", "", "4970"),
    ("Sonstiges", "", "4980"),
]


def seed(apps, schema_editor):
    SKR03Account = apps.get_model("finance", "SKR03Account")
    AccountMapping = apps.get_model("finance", "AccountMapping")

    accounts_by_number = {}
    for number, name in SKR03_ACCOUNTS:
        account, _ = SKR03Account.objects.get_or_create(number=number, defaults={"name": name})
        accounts_by_number[number] = account

    for art, variante, number in ACCOUNT_MAPPINGS:
        AccountMapping.objects.get_or_create(
            art=art, variante=variante, defaults={"skr03_account": accounts_by_number[number]}
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0007_remove_expense_account_debit_target_eur_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, noop),
    ]
