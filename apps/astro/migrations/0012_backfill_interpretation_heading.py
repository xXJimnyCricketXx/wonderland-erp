# Backfuellt das neue heading-Feld fuer bereits bestehende Zeilen mit dem
# bisherigen, fest aus text_type abgeleiteten Label - sonst wuerden alle
# schon vorhandenen Auswertungstexte (z.B. der bereits geschriebene
# Sonne/Fische-Text) beim Speichern ploetzlich ohne Zwischenueberschrift im
# Report erscheinen. "Der konstruktive [Zeichen]"/"Der problematische
# [Zeichen]" werden bewusst 1:1 mituebernommen (nicht automatisch korrigiert,
# da Artikel/Endung vom Zeichen abhaengen) - die Redaktion korrigiert diese
# beiden Faelle anschliessend manuell pro Zeile.
from django.db import migrations

OLD_LABELS = {
    "grund": "Allgemeine Beschreibung (Grundtext)",
    "konstruktiv": "Der konstruktive [Zeichen]",
    "problematisch": "Der problematische [Zeichen]",
    "gegenteil": "Das Gegenteil der Eigenschaften",
    "beziehung": "Freundschaft/Partnerschaft/Liebe",
    "beruf": "Beruf",
    "kindheit": "Kindheit",
    "aufgaben_karma": "Aufgaben/Karma/Gesundheit",
    "entsprechungen": "Entsprechungen",
    "erfuellt": "Die erfüllte Seite",
    "unerfuellt": "Die unerfüllte Seite",
    "psychologisches": "Psychologisches",
    "gesundheit": "Gesundheit (Kurzform)",
}


def backfill_heading(apps, schema_editor):
    InterpretationText = apps.get_model("astro", "InterpretationText")
    for text_type, label in OLD_LABELS.items():
        InterpretationText.objects.filter(text_type=text_type, heading="").update(heading=label)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('astro', '0011_interpretationtext_heading'),
    ]

    operations = [
        migrations.RunPython(backfill_heading, noop),
    ]
