from django.db import migrations

# Moderner Herrscher (nicht der klassische) bei Skorpion/Wassermann/Fische -
# astroschmids eigene Vorlagen nutzen ebenfalls Pluto/Uranus/Neptun statt
# Mars/Saturn/Jupiter, siehe ZodiacSign.ruler_planet-Kommentar.
RULER_BY_SIGN_KEY = {
    "widder": "mars",
    "stier": "venus",
    "zwillinge": "merkur",
    "krebs": "mond",
    "loewe": "sonne",
    "jungfrau": "merkur",
    "waage": "venus",
    "skorpion": "pluto",
    "schuetze": "jupiter",
    "steinbock": "saturn",
    "wassermann": "uranus",
    "fische": "neptun",
}


def seed(apps, schema_editor):
    ZodiacSign = apps.get_model("astro", "ZodiacSign")
    Planet = apps.get_model("astro", "Planet")
    db_alias = schema_editor.connection.alias

    planets_by_key = {p.key: p for p in Planet.objects.using(db_alias).all()}
    for sign_key, planet_key in RULER_BY_SIGN_KEY.items():
        ZodiacSign.objects.using(db_alias).filter(key=sign_key).update(
            ruler_planet=planets_by_key[planet_key]
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('astro', '0005_themenbild_alter_interpretationtext_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, noop),
    ]
