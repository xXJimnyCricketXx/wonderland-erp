# Ersetzt den kompletten Inhalt der vorherigen SKR03-Seed-Migration
# (0008_seed_skr03_accounts) 1:1 durch die vom Nutzer gelieferte
# testdata/skr03_mapping.json - deutlich umfangreicher (40 Konten, 45
# Art/Variante-Zuordnungen über 19 Ausgaben-Kategorien statt der
# ursprünglichen 9). Alte SKR03Account/AccountMapping-Zeilen werden
# entfernt, bevor die neuen angelegt werden.
from django.db import migrations

SKR03_ACCOUNTS = [
    ('3010', 'Einkauf Roh-, Hilfs- und Betriebsstoffe 7 % Vorsteuer'),
    ('3030', 'Einkauf Roh-, Hilfs- und Betriebsstoffe 19 % Vorsteuer'),
    ('3300', 'Wareneingang 7 %'),
    ('3400', 'Wareneingang 19 %'),
    ('4380', 'Beiträge'),
    ('4600', 'Werbekosten'),
    ('4605', 'Streuartikel'),
    ('4710', 'Verpackungsmaterial'),
    ('4760', 'Verkaufsprovisionen'),
    ('4855', 'Sofortabschreibung geringwertiger Wirtschaftsgüter (GWG bis 250 € netto)'),
    ('0480', 'Geringwertige Wirtschaftsgüter (GWG 250,01-800 € netto, Sammelposten/Pool)'),
    ('4900', 'Sonstige betriebliche Aufwendungen'),
    ('4910', 'Porto'),
    ('4930', 'Bürobedarf'),
    ('4980', 'Sonstiger Betriebsbedarf'),
    ('4985', 'Werkzeuge und Kleingeräte'),
    ('3062', 'Einkauf Roh-, Hilfs- und Betriebsstoffe, innergem. Erwerb 19 % Vorsteuer und 19 % Umsatzsteuer'),
    ('3425', 'Innergemeinschaftlicher Erwerb 19 % Vorsteuer und 19 % Umsatzsteuer (Wareneingang)'),
    ('3850', 'Zölle und Einfuhrabgaben'),
    ('4287', 'Tagespauschale für die Tätigkeit in der häuslichen Wohnung'),
    ('4288', 'Aufwendungen für ein häusliches Arbeitszimmer (abziehbarer Anteil)'),
    ('4360', 'Versicherungen'),
    ('4530', 'Laufende Fahrzeug-Betriebskosten'),
    ('4670', 'Reisekosten Unternehmer'),
    ('4673', 'Reisekosten Unternehmer Fahrtkosten'),
    ('4674', 'Reisekosten Unternehmer Verpflegungsmehraufwand'),
    ('4676', 'Reisekosten Unternehmer Übernachtungsaufwand und Reisenebenkosten'),
    ('4750', 'Transportversicherungen'),
    ('4806', 'Wartungskosten für Hard- und Software'),
    ('4920', 'Telefon'),
    ('4925', 'Internetkosten'),
    ('4940', 'Zeitschriften, Bücher, digitale Medien (Fachliteratur)'),
    ('4945', 'Fortbildungskosten'),
    ('4950', 'Rechts- und Beratungskosten'),
    ('4955', 'Buchführungskosten'),
    ('4970', 'Nebenkosten des Geldverkehrs'),
    ('0027', 'EDV-Software (Anlagevermögen)'),
    ('0030', 'Lizenzen an gewerblichen Schutzrechten und ähnlichen Rechten und Werten (Anlagevermögen)'),
    ('0400', 'Betriebsausstattung'),
    ('0430', 'Ladeneinrichtung'),
]

# (art, variante, skr03_nummer) - "art" ersetzt die alten expense_category-
# Werte vollständig (siehe core/reference_data.py, DEFAULT_SEED_DATA
# "expense_category" wurde im selben Zug auf diese 19 Werte umgestellt).
ACCOUNT_MAPPINGS = [
    ('Waren / Handel', 'Einkauf 7% USt', '3300'),
    ('Waren / Handel', 'Einkauf 19% USt', '3400'),
    ('Waren / Verbrauch', 'Einkauf 7% USt', '3010'),
    ('Waren / Verbrauch', 'Einkauf 19% USt', '3030'),
    ('Verpackung / Porto', 'Verpackungsmaterial', '4710'),
    ('Verpackung / Porto', 'Porto / Versandkosten', '4910'),
    ('Bürobedarf', 'Allgemein', '4930'),
    ('Kleinmaterialien / Werkstattbedarf', 'Werkzeug / Kleingerät', '4985'),
    ('Kleinmaterialien / Werkstattbedarf', 'Verbrauchsmaterial (Kleben, Kabel, Kleinteile)', '4980'),
    ('GWG', 'Sofortaufwand bis 250 € netto', '4855'),
    ('GWG', 'Sofort/Pool 250,01-800 € netto', '0480'),
    ('Dekomaterial / Werbekosten', 'Werbung / Marketing allgemein', '4600'),
    ('Dekomaterial / Werbekosten', 'Streuartikel / Give-aways', '4605'),
    ('Gebühren', 'Transaktions-/Einstellgebühren Etsy', '4760'),
    ('Gebühren', 'Marketinggebühr Etsy (Offsite Ads)', '4600'),
    ('Gebühren', 'Rückerstattung Etsy-Gebühren', '4760'),
    ('Gebühren', 'Verpackungslizenz (Duales System / LUCID)', '4710'),
    ('Gebühren', 'Mitgliedsbeitrag Verein', '4380'),
    ('Gebühren', 'Postfachmiete', '4900'),
    ('Gebühren', 'Sonstige Gebühr', '4900'),
    ('Gebühren', 'Bank-/Kontoführungsgebühren (PayPal, Auslandsüberweisung etc.)', '4970'),
    ('Sonstiges', 'Allgemein', '4900'),
    ('Waren / Handel', 'Einkauf EU (innergem. Erwerb) 19% USt', '3425'),
    ('Waren / Verbrauch', 'Einkauf EU (innergem. Erwerb) 19% USt', '3062'),
    ('Waren / Handel', 'Zölle/Einfuhrabgaben (Drittlandimport)', '3850'),
    ('Reisekosten Unternehmer', 'Fahrtkosten (Mineralienbörse/Einkaufsreise)', '4673'),
    ('Reisekosten Unternehmer', 'Verpflegungsmehraufwand', '4674'),
    ('Reisekosten Unternehmer', 'Übernachtung/Reisenebenkosten', '4676'),
    ('Reisekosten Unternehmer', 'Sonstige Reisekosten (allgemein)', '4670'),
    ('Kfz-Kosten', 'Laufende Betriebskosten', '4530'),
    ('Telefon/Internet', 'Telefon', '4920'),
    ('Telefon/Internet', 'Internet', '4925'),
    ('Software/EDV', 'Wartung/Abo laufend', '4806'),
    ('Software/EDV', 'Kauf (Anlagevermögen, AfA 1 Jahr)', '0027'),
    ('Software/EDV', 'Lifetime-Lizenz (Anlagevermögen)', '0030'),
    ('Fortbildung', 'Kurs/Seminar (z.B. Gemmologie/Steinheilkunde)', '4945'),
    ('Fachliteratur', 'Bücher/Zeitschriften/digitale Medien', '4940'),
    ('Beratungskosten', 'Steuerberater/Rechtsberatung', '4950'),
    ('Beratungskosten', 'Buchführung (Software/Dienstleister)', '4955'),
    ('Versicherung', 'Transportversicherung (Edelsteinversand)', '4750'),
    ('Versicherung', 'Betriebshaftpflicht/Inhaltsversicherung', '4360'),
    ('Arbeitszimmer', 'Tagespauschale', '4287'),
    ('Arbeitszimmer', 'Häusliches Arbeitszimmer (abziehbarer Anteil)', '4288'),
    ('Betriebsausstattung (Anlagevermögen)', 'Regale/Möbel/Einrichtung (Aktivierung > 800 € netto)', '0400'),
    ('Betriebsausstattung (Anlagevermögen)', 'Standausstattung Messe/Markt', '0430'),
]

EXPENSE_CATEGORIES = [
    "Waren / Handel", "Waren / Verbrauch", "Verpackung / Porto", "Bürobedarf",
    "Kleinmaterialien / Werkstattbedarf", "GWG", "Dekomaterial / Werbekosten",
    "Gebühren", "Sonstiges", "Reisekosten Unternehmer", "Kfz-Kosten",
    "Telefon/Internet", "Software/EDV", "Fortbildung", "Fachliteratur",
    "Beratungskosten", "Versicherung", "Arbeitszimmer",
    "Betriebsausstattung (Anlagevermögen)",
]


def replace(apps, schema_editor):
    SKR03Account = apps.get_model("finance", "SKR03Account")
    AccountMapping = apps.get_model("finance", "AccountMapping")
    ReferenceOption = apps.get_model("core", "ReferenceOption")

    AccountMapping.objects.all().delete()
    SKR03Account.objects.all().delete()

    accounts_by_number = {}
    for number, name in SKR03_ACCOUNTS:
        account, _ = SKR03Account.objects.get_or_create(number=number, defaults={"name": name})
        accounts_by_number[number] = account

    for art, variante, number in ACCOUNT_MAPPINGS:
        AccountMapping.objects.get_or_create(
            art=art, variante=variante, defaults={"skr03_account": accounts_by_number[number]}
        )

    ReferenceOption.objects.filter(category="expense_category").delete()
    for order, value in enumerate(EXPENSE_CATEGORIES):
        ReferenceOption.objects.get_or_create(
            category="expense_category", value=value, defaults={"order": order}
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0008_seed_skr03_accounts'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(replace, noop),
    ]
