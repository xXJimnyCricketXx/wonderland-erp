from django.db import migrations

# Astrologisches Lehrbuchwissen (Elemente/Qualitaeten/Haeuser-Grundbedeutungen)
# - Jahrzehnte alte, freie Grundlagen, keine Uebernahme einzelner
# kommerzieller Anbietertexte, siehe Umsetzungsplan Phase 0.
ZODIAC_SIGNS = [
    ("widder", "Widder", "♈", "feuer", "kardinal", "mars", 1),
    ("stier", "Stier", "♉", "erde", "fix", "venus", 2),
    ("zwillinge", "Zwillinge", "♊", "luft", "veraenderlich", "merkur", 3),
    ("krebs", "Krebs", "♋", "wasser", "kardinal", "mond", 4),
    ("loewe", "Löwe", "♌", "feuer", "fix", "sonne", 5),
    ("jungfrau", "Jungfrau", "♍", "erde", "veraenderlich", "merkur", 6),
    ("waage", "Waage", "♎", "luft", "kardinal", "venus", 7),
    ("skorpion", "Skorpion", "♏", "wasser", "fix", "pluto", 8),
    ("schuetze", "Schütze", "♐", "feuer", "veraenderlich", "jupiter", 9),
    ("steinbock", "Steinbock", "♑", "erde", "kardinal", "saturn", 10),
    ("wassermann", "Wassermann", "♒", "luft", "fix", "uranus", 11),
    ("fische", "Fische", "♓", "wasser", "veraenderlich", "neptun", 12),
]

# key muss zu ephemeris.py's PLANET_KEYS passen (siehe services/ephemeris.py).
PLANETS = [
    ("sonne", "Sonne", False, False),
    ("mond", "Mond", False, False),
    ("merkur", "Merkur", False, False),
    ("venus", "Venus", False, False),
    ("mars", "Mars", False, False),
    ("jupiter", "Jupiter", False, False),
    ("saturn", "Saturn", False, False),
    ("uranus", "Uranus", False, False),
    ("neptun", "Neptun", False, False),
    ("pluto", "Pluto", False, False),
    ("chiron", "Chiron", False, True),
    ("pholus", "Pholus", False, True),
    ("lilith", "Lilith", False, True),
    ("aszendent", "Aszendent", True, False),
    ("mc", "Medium Coeli (MC)", True, False),
]

HOUSES = [
    (1, "Selbst", "Identität, Auftreten, Körper"),
    (2, "Besitz", "Materielle Sicherheit, Werte, Selbstwert"),
    (3, "Kommunikation", "Denken, Sprache, nahe Umgebung"),
    (4, "Familie/Zuhause", "Wurzeln, Zuhause, Familie"),
    (5, "Kreativität", "Kreativität, Liebe, Kinder"),
    (6, "Alltag/Gesundheit", "Arbeit, Alltag, Gesundheit"),
    (7, "Partnerschaft", "Partnerschaft, Begegnung"),
    (8, "Wandlung", "Transformation, Intimität, Krisen"),
    (9, "Philosophie", "Reisen, Philosophie, höhere Bildung"),
    (10, "Berufung/Status", "Beruf, Status, öffentliches Leben"),
    (11, "Freundschaft", "Freundschaft, Netzwerke, Zukunftsvisionen"),
    (12, "Unbewusstes", "Unbewusstes, Rückzug, Spiritualität"),
]


def seed(apps, schema_editor):
    ZodiacSign = apps.get_model("astro", "ZodiacSign")
    Planet = apps.get_model("astro", "Planet")
    House = apps.get_model("astro", "House")
    db_alias = schema_editor.connection.alias

    for key, name_de, symbol, element, quality, ruling_planet_key, sort_order in ZODIAC_SIGNS:
        ZodiacSign.objects.using(db_alias).update_or_create(
            key=key,
            defaults=dict(
                name_de=name_de, symbol=symbol, element=element,
                quality=quality, ruling_planet_key=ruling_planet_key, sort_order=sort_order,
            ),
        )

    for key, name_de, is_angle, is_optional_body in PLANETS:
        Planet.objects.using(db_alias).update_or_create(
            key=key,
            defaults=dict(name_de=name_de, is_angle=is_angle, is_optional_body=is_optional_body),
        )

    for number, name_de, short_meaning in HOUSES:
        House.objects.using(db_alias).update_or_create(
            number=number,
            defaults=dict(name_de=name_de, short_meaning=short_meaning),
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('astro', '0002_geocodecache'),
    ]

    operations = [
        migrations.RunPython(seed, noop),
    ]
